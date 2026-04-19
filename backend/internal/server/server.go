package server

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type Task struct {
	ID          int64     `json:"id"`
	Title       string    `json:"title"`
	Completed   bool      `json:"completed"`
	UpdatedAt   time.Time `json:"updated_at"`
	Description string    `json:"description"`
}

type Telemetry struct {
	TraceID    string         `json:"trace_id"`
	SpanName   string         `json:"span_name"`
	Duration   float64        `json:"duration_ms"`
	Attributes map[string]any `json:"attributes"`
}

type Store struct {
	mu             sync.Mutex
	tasks          map[int64]Task
	telemetry      []Telemetry
	nextID         int64
	requestsTotal  uint64
	activeRequests int64
	taskOps        map[string]uint64
	ready          atomic.Bool
}

func NewStore() *Store {
	store := &Store{
		tasks:     make(map[int64]Task),
		telemetry: make([]Telemetry, 0),
		nextID:    1,
		taskOps:   make(map[string]uint64),
	}
	store.ready.Store(true)
	return store
}

func Handler(store *Store) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", instrument(store, func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	}))
	mux.HandleFunc("/ready", instrument(store, func(w http.ResponseWriter, _ *http.Request) {
		if !store.ready.Load() {
			http.Error(w, "not ready", http.StatusServiceUnavailable)
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "ready"})
	}))
	mux.HandleFunc("/metrics", instrument(store, func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		fmt.Fprintf(w, "http_requests_total %d\n", atomic.LoadUint64(&store.requestsTotal))
		fmt.Fprintf(w, "active_connections %d\n", atomic.LoadInt64(&store.activeRequests))
		store.mu.Lock()
		defer store.mu.Unlock()
		for operation, total := range store.taskOps {
			fmt.Fprintf(w, "task_operations_total{operation=%q} %d\n", operation, total)
		}
	}))
	mux.HandleFunc("/telemetry", instrument(store, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var payload Telemetry
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, "invalid telemetry payload", http.StatusBadRequest)
			return
		}
		store.mu.Lock()
		store.telemetry = append(store.telemetry, payload)
		store.mu.Unlock()
		writeJSON(w, http.StatusAccepted, map[string]string{"status": "accepted"})
	}))
	mux.HandleFunc("/tasks", instrument(store, func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			store.incrementTaskOp("list")
			tasks := store.listTasks()
			writeJSON(w, http.StatusOK, tasks)
		case http.MethodPost:
			var input Task
			if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
				http.Error(w, "invalid task payload", http.StatusBadRequest)
				return
			}
			store.incrementTaskOp("create")
			task := store.createTask(input)
			writeJSON(w, http.StatusCreated, task)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}))
	mux.HandleFunc("/tasks/", instrument(store, func(w http.ResponseWriter, r *http.Request) {
		idValue := strings.TrimPrefix(r.URL.Path, "/tasks/")
		id, err := strconv.ParseInt(idValue, 10, 64)
		if err != nil {
			http.Error(w, "invalid task id", http.StatusBadRequest)
			return
		}
		switch r.Method {
		case http.MethodPut:
			var input Task
			if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
				http.Error(w, "invalid task payload", http.StatusBadRequest)
				return
			}
			task, ok := store.updateTask(id, input)
			if !ok {
				http.NotFound(w, r)
				return
			}
			store.incrementTaskOp("update")
			writeJSON(w, http.StatusOK, task)
		case http.MethodDelete:
			if !store.deleteTask(id) {
				http.NotFound(w, r)
				return
			}
			store.incrementTaskOp("delete")
			w.WriteHeader(http.StatusNoContent)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}))
	return mux
}

func instrument(store *Store, next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		atomic.AddUint64(&store.requestsTotal, 1)
		atomic.AddInt64(&store.activeRequests, 1)
		defer atomic.AddInt64(&store.activeRequests, -1)

		traceID := r.Header.Get("Traceparent")
		if traceID == "" {
			traceID = "local-trace"
		}
		ctx := context.WithValue(r.Context(), traceKey{}, traceID)
		next(w, r.WithContext(ctx))
	}
}

type traceKey struct{}

func TraceID(ctx context.Context) string {
	value, _ := ctx.Value(traceKey{}).(string)
	return value
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func (store *Store) createTask(input Task) Task {
	store.mu.Lock()
	defer store.mu.Unlock()
	task := Task{
		ID:          store.nextID,
		Title:       input.Title,
		Description: input.Description,
		Completed:   input.Completed,
		UpdatedAt:   time.Now().UTC(),
	}
	store.tasks[task.ID] = task
	store.nextID++
	return task
}

func (store *Store) listTasks() []Task {
	store.mu.Lock()
	defer store.mu.Unlock()
	tasks := make([]Task, 0, len(store.tasks))
	for _, task := range store.tasks {
		tasks = append(tasks, task)
	}
	sort.Slice(tasks, func(i, j int) bool {
		return tasks[i].ID < tasks[j].ID
	})
	return tasks
}

func (store *Store) updateTask(id int64, input Task) (Task, bool) {
	store.mu.Lock()
	defer store.mu.Unlock()
	task, ok := store.tasks[id]
	if !ok {
		return Task{}, false
	}
	task.Title = input.Title
	task.Description = input.Description
	task.Completed = input.Completed
	task.UpdatedAt = time.Now().UTC()
	store.tasks[id] = task
	return task, true
}

func (store *Store) deleteTask(id int64) bool {
	store.mu.Lock()
	defer store.mu.Unlock()
	if _, ok := store.tasks[id]; !ok {
		return false
	}
	delete(store.tasks, id)
	return true
}

func (store *Store) incrementTaskOp(operation string) {
	store.mu.Lock()
	defer store.mu.Unlock()
	store.taskOps[operation]++
}

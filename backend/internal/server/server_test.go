package server

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHealthEndpoint(t *testing.T) {
	handler := Handler(NewStore())
	request := httptest.NewRequest(http.MethodGet, "/health", nil)
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)

	if response.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", response.Code)
	}
}

func TestTaskCRUD(t *testing.T) {
	handler := Handler(NewStore())
	body, _ := json.Marshal(Task{Title: "Inspect traces", Description: "Correlate mobile to backend", Completed: false})
	createRequest := httptest.NewRequest(http.MethodPost, "/tasks", bytes.NewReader(body))
	createResponse := httptest.NewRecorder()
	handler.ServeHTTP(createResponse, createRequest)

	if createResponse.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d", createResponse.Code)
	}

	updateBody, _ := json.Marshal(Task{Title: "Inspect traces", Description: "Updated", Completed: true})
	updateRequest := httptest.NewRequest(http.MethodPut, "/tasks/1", bytes.NewReader(updateBody))
	updateResponse := httptest.NewRecorder()
	handler.ServeHTTP(updateResponse, updateRequest)

	if updateResponse.Code != http.StatusOK {
		t.Fatalf("expected 200 on update, got %d", updateResponse.Code)
	}

	listRequest := httptest.NewRequest(http.MethodGet, "/tasks", nil)
	listResponse := httptest.NewRecorder()
	handler.ServeHTTP(listResponse, listRequest)
	if !strings.Contains(listResponse.Body.String(), "Inspect traces") {
		t.Fatal("expected created task in list response")
	}

	deleteRequest := httptest.NewRequest(http.MethodDelete, "/tasks/1", nil)
	deleteResponse := httptest.NewRecorder()
	handler.ServeHTTP(deleteResponse, deleteRequest)
	if deleteResponse.Code != http.StatusNoContent {
		t.Fatalf("expected 204, got %d", deleteResponse.Code)
	}
}

func TestMetricsExposed(t *testing.T) {
	store := NewStore()
	handler := Handler(store)
	createBody, _ := json.Marshal(Task{Title: "Inspect traces", Description: "Correlate mobile to backend", Completed: false})
	createRequest := httptest.NewRequest(http.MethodPost, "/tasks", bytes.NewReader(createBody))
	createResponse := httptest.NewRecorder()
	handler.ServeHTTP(createResponse, createRequest)

	request := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	if response.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", response.Code)
	}
	if !strings.Contains(response.Body.String(), "http_requests_total") {
		t.Fatal("expected metrics body to include http_requests_total")
	}
	if !strings.Contains(response.Body.String(), `task_operations_total{operation="create"} 1`) {
		t.Fatal("expected task operation metric for create")
	}
}

func TestTracing(t *testing.T) {
	store := NewStore()
	handler := Handler(store)
	body := []byte(`{"trace_id":"abc123","span_name":"mobile.tap","duration_ms":12.4,"attributes":{"screen":"home"}}`)
	request := httptest.NewRequest(http.MethodPost, "/telemetry", bytes.NewReader(body))
	request.Header.Set("Traceparent", "00-1234567890abcdef-1234567890abcdef-01")
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	if response.Code != http.StatusAccepted {
		t.Fatalf("expected 202, got %d", response.Code)
	}
	if len(store.telemetry) != 1 {
		t.Fatal("expected telemetry to be recorded")
	}
}

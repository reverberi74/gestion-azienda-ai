<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;

class AiController extends Controller
{
    public function chat(Request $request): JsonResponse
    {
        $requestId = (string) Str::uuid();

        try {
            $validated = $request->validate([
                'tenant_id' => ['required', 'string', 'max:64'],
                'skill'     => ['required', 'string', 'max:64'],
                'query'     => ['required', 'string', 'max:4000'],
                'locale'    => ['nullable', 'string', 'max:16'],
                'metadata'  => ['nullable', 'array'],
            ]);
        } catch (ValidationException $e) {
            // Forziamo sempre JSON (evita redirect/HTML quando manca Accept header)
            return response()->json([
                'message' => $e->getMessage(),
                'errors'  => $e->errors(),
            ], 422);
        }

        $baseUrl = rtrim((string) config('ai.service_base_url', 'http://127.0.0.1:8001'), '/');
        $token   = trim((string) config('ai.internal_token', ''));
        $timeout = (int) config('ai.timeout_seconds', 8);

        if ($token === '') {
            return response()->json([
                'error' => [
                    'code'       => 'AI_NOT_CONFIGURED',
                    'message'    => 'AI_INTERNAL_TOKEN not configured',
                    'request_id' => $requestId,
                ],
            ], 500);
        }

        try {
            $resp = Http::timeout($timeout)
                ->acceptJson()
                ->asJson()
                ->withHeaders([
                    'X-AI-Internal-Token' => $token,
                    'X-Request-Id'        => $requestId,
                ])
                ->post($baseUrl . '/v1/ai/chat', $validated);

            if ($resp->successful()) {
                return response()->json($resp->json(), 200);
            }

            return response()->json([
                'error' => [
                    'code'        => 'AI_PROVIDER_ERROR',
                    'message'     => 'AI service returned an error',
                    'http_status' => $resp->status(),
                    'request_id'  => $requestId,
                    'details'     => $resp->json(),
                ],
            ], 502);
        } catch (\Throwable $e) {
            return response()->json([
                'error' => [
                    'code'       => 'AI_SERVICE_DOWN',
                    'message'    => 'AI service not reachable',
                    'request_id' => $requestId,
                ],
            ], 503);
        }
    }
}

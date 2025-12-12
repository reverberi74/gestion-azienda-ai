<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Http;

class HealthController extends Controller
{
    /**
     * Health semplice di Laravel.
     */
    public function index(): JsonResponse
    {
        return response()->json([
            'status'  => 'ok',
            'service' => 'laravel',
            'env'     => config('app.env'),
        ]);
    }

    /**
     * Health combinato Laravel + service-ai.
     */
    public function ai(): JsonResponse
    {
        $result = [
            'laravel' => [
                'status' => 'ok',
                'env'    => config('app.env'),
            ],
        ];

        // Base URL del servizio AI (da .env)
        $baseUrl = rtrim(env('AI_SERVICE_BASE_URL', 'http://127.0.0.1:8001'), '/');

        try {
            $response = Http::timeout(2)->get($baseUrl . '/v1/health');

            $result['service_ai'] = [
                'status'      => $response->successful() ? 'ok' : 'error',
                'http_status' => $response->status(),
                'body'        => $response->json(),
            ];
        } catch (\Throwable $e) {
            $result['service_ai'] = [
                'status' => 'down',
                'error'  => $e->getMessage(), // in prod poi possiamo “pulire” il messaggio
            ];
        }

        return response()->json($result);
    }
}

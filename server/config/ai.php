<?php

return [
    /*
    |--------------------------------------------------------------------------
    | AI Service
    |--------------------------------------------------------------------------
    | Config centralizzata per comunicazione Laravel -> service-ai.
    | Usare config() evita sorprese con env() e config caching.
    */

    'service_base_url' => env('AI_SERVICE_BASE_URL', 'http://127.0.0.1:8001'),

    /*
    |--------------------------------------------------------------------------
    | Internal Token (Laravel -> service-ai)
    |--------------------------------------------------------------------------
    | Token condiviso per proteggere endpoint interni del microservizio.
    | NON loggare mai il valore in chiaro.
    */
    'internal_token' => env('AI_INTERNAL_TOKEN', ''),

    /*
    |--------------------------------------------------------------------------
    | HTTP client settings
    |--------------------------------------------------------------------------
    */
    'timeout_seconds' => (int) env('AI_SERVICE_TIMEOUT', 8),
];

<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\HealthController;
use App\Http\Controllers\Api\AiController;

Route::prefix('v1')->group(function () {
    Route::get('/health', [HealthController::class, 'index']);
    Route::get('/health/ai', [HealthController::class, 'ai']);

    Route::post('/ai/chat', [AiController::class, 'chat']);
});

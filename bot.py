from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from functools import wraps
import jwt
import datetime
import sqlite3
import hashlib
import requests
import os
import re
from urllib.parse import urlparse
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'diablo_system_secret_key_2024_change_in_production_secure'
app.config['SESSION_TYPE'] = 'filesystem'

# Güvenlik önlemleri - Rate limiting
request_times = {}

# SQL Injection koruma
def sanitize_input(input_str):
    if not input_str:
        return input_str
    # SQL injection pattern'leri
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER|CREATE|TRUNCATE)\b)',
        r'(\b(OR|AND)\b.*=)',
        r'(\b(SLEEP|WAITFOR|DELAY)\b)',
        r'(\-\-|\#|\/\*)',
        r'(\b(LOAD_FILE|OUTFILE|DUMPFILE)\b)',
        r'(\b(XP_|SP_)\w+)'
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, input_str, re.IGNORECASE):
            raise ValueError("Geçersiz karakterler tespit edildi")
    
    # HTML/JS injection koruma
    input_str = re.sub(r'<script.*?>.*?</script>', '', input_str, flags=re.IGNORECASE)
    input_str = re.sub(r'<.*?javascript:.*?>', '', input_str, flags=re.IGNORECASE)
    input_str = re.sub(r'on\w+=', '', input_str, flags=re.IGNORECASE)
    
    return input_str.strip()

# Rate limiting
def check_rate_limit(ip, limit=10, window=60):
    now = time.time()
    if ip not in request_times:
        request_times[ip] = []
    
    # Eski istekleri temizle
    request_times[ip] = [t for t in request_times[ip] if now - t < window]
    
    # Rate limit kontrolü
    if len(request_times[ip]) >= limit:
        return False
    
    request_times[ip].append(now)
    return True

# IP bazlı güvenlik
def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

# HTML Template'leri - Cam Efekti Eklendi
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diablo System - Giriş</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: url('https://i.ibb.co/jPbg5kQr/V-D-20251129-121335-350.gif') no-repeat center center fixed;
            background-size: cover;
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .login-container {
            width: 100%;
            max-width: 400px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .login-icon {
            font-size: 60px;
            color: #ff0000;
            margin-bottom: 15px;
            text-shadow: 0 0 15px rgba(255, 0, 0, 0.7);
        }

        .login-header h1 {
            font-size: 28px;
            color: #ff0000;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
            margin-bottom: 10px;
        }

        .login-header p {
            color: #fff;
            font-size: 14px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #ff0000;
            font-weight: bold;
            font-size: 14px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .form-control {
            width: 100%;
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            color: #fff;
            font-size: 16px;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
        }

        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }

        .form-control:focus {
            outline: none;
            border-color: #ff0000;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.5);
            background: rgba(255, 255, 255, 0.2);
        }

        .btn {
            width: 100%;
            background: linear-gradient(45deg, #ff0000, #ff4444);
            color: #fff;
            border: none;
            padding: 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
            margin-top: 10px;
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.4);
            backdrop-filter: blur(5px);
        }

        .btn:hover {
            background: linear-gradient(45deg, #ff4444, #ff0000);
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(255, 0, 0, 0.6);
        }

        .admin-link {
            text-align: center;
            margin-top: 20px;
        }

        .admin-link a {
            color: #ff0000;
            text-decoration: none;
            font-size: 14px;
            transition: all 0.3s;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .admin-link a:hover {
            text-decoration: underline;
            text-shadow: 0 0 5px rgba(255, 0, 0, 0.7);
        }

        .alert {
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 5px;
            text-align: center;
            display: none;
            backdrop-filter: blur(5px);
        }

        .alert-error {
            background: rgba(255, 0, 0, 0.2);
            border: 1px solid rgba(255, 0, 0, 0.5);
            color: #ff6b6b;
        }

        .vip-info {
            background: rgba(255, 215, 0, 0.15);
            border: 1px solid rgba(255, 215, 0, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            text-align: center;
            backdrop-filter: blur(5px);
        }

        .vip-info h3 {
            color: #ffd700;
            margin-bottom: 10px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .vip-info p {
            color: #fff;
            font-size: 14px;
            margin-bottom: 5px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .vip-link {
            color: #ffd700;
            text-decoration: none;
            font-weight: bold;
            display: block;
            margin-top: 10px;
            padding: 8px;
            background: rgba(255, 215, 0, 0.2);
            border-radius: 5px;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
        }

        .vip-link:hover {
            background: rgba(255, 215, 0, 0.3);
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.7);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <div class="login-icon">
                <i class="fas fa-fire"></i>
            </div>
            <h1>DİABLO SYSTEM</h1>
            <p>Güvenli Giriş Paneli</p>
        </div>

        <div class="alert alert-error" id="errorAlert"></div>
        <div class="alert alert-success" id="successAlert"></div>

        <form id="loginForm">
            <div class="form-group">
                <label for="username">Kullanıcı Adı</label>
                <input type="text" id="username" name="username" class="form-control" placeholder="Kullanıcı adınız" required>
            </div>
            <div class="form-group">
                <label for="password">Şifre</label>
                <input type="password" id="password" name="password" class="form-control" placeholder="Şifreniz" required>
            </div>
            <button type="submit" class="btn">
                <i class="fas fa-sign-in-alt"></i> Giriş Yap
            </button>
        </form>

        <div class="admin-link">
            <a href="#" id="adminLoginLink">Admin Girişi</a>
        </div>

        <div class="vip-info">
            <h3><i class="fas fa-crown"></i> VIP SATIN AL</h3>
            <p>Discord: @tanridiablo</p>
            <p>Telegram: @diablopa</p>
            <a href="https://t.me/diablopa" class="vip-link" target="_blank">
                <i class="fab fa-telegram"></i> VIP Satın Almak İçin Tıkla
            </a>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({username, password})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    localStorage.setItem('token', data.token);
                    localStorage.setItem('user_type', data.user_type);
                    localStorage.setItem('vip_status', data.vip_status);
                    localStorage.setItem('username', data.username);
                    window.location.href = '/panel';
                } else {
                    showError(data.message);
                }
            })
            .catch(error => {
                showError('Giriş sırasında hata oluştu: ' + error.message);
            });
        });

        document.getElementById('adminLoginLink').addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('username').value = 'admin';
            document.getElementById('password').focus();
        });

        function showError(message) {
            const errorAlert = document.getElementById('errorAlert');
            errorAlert.textContent = message;
            errorAlert.style.display = 'block';
            
            setTimeout(() => {
                errorAlert.style.display = 'none';
            }, 5000);
        }

        function showSuccess(message) {
            const successAlert = document.getElementById('successAlert');
            successAlert.textContent = message;
            successAlert.style.display = 'block';
            
            setTimeout(() => {
                successAlert.style.display = 'none';
            }, 5000);
        }
    </script>
</body>
</html>
'''

VIP_PROMO_HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIP Üyelik - Diablo System</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: url('https://i.ibb.co/jPbg5kQr/V-D-20251129-121335-350.gif') no-repeat center center fixed;
            background-size: cover;
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .vip-container {
            width: 100%;
            max-width: 500px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 0 50px rgba(255, 215, 0, 0.5);
            border: 2px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        }

        .vip-icon {
            font-size: 80px;
            color: #ffd700;
            margin-bottom: 20px;
            text-shadow: 0 0 20px rgba(255, 215, 0, 0.7);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .vip-title {
            font-size: 32px;
            color: #ffd700;
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.7);
        }

        .vip-message {
            font-size: 18px;
            color: #fff;
            margin-bottom: 30px;
            line-height: 1.6;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .vip-features {
            text-align: left;
            margin-bottom: 30px;
            background: rgba(255, 215, 0, 0.15);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 215, 0, 0.3);
            backdrop-filter: blur(5px);
        }

        .vip-features h3 {
            color: #ffd700;
            margin-bottom: 15px;
            text-align: center;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            color: #fff;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .feature-item i {
            color: #ffd700;
            margin-right: 10px;
            font-size: 14px;
        }

        .vip-contact {
            background: rgba(255, 0, 0, 0.15);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 0, 0, 0.3);
            margin-bottom: 20px;
            backdrop-filter: blur(5px);
        }

        .vip-contact h3 {
            color: #ff0000;
            margin-bottom: 15px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .contact-info {
            color: #fff;
            margin-bottom: 10px;
            font-size: 16px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .telegram-btn {
            display: inline-block;
            background: linear-gradient(45deg, #0088cc, #00aced);
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            font-size: 18px;
            margin: 10px 0;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(0, 136, 204, 0.4);
            backdrop-filter: blur(5px);
        }

        .telegram-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 136, 204, 0.6);
        }

        .telegram-btn i {
            margin-right: 10px;
        }

        .back-btn {
            display: inline-block;
            background: rgba(255, 255, 255, 0.15);
            color: #fff;
            padding: 12px 25px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 15px;
            transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(5px);
        }

        .back-btn:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="vip-container">
        <div class="vip-icon">
            <i class="fas fa-crown"></i>
        </div>
        
        <h1 class="vip-title">VIP ÜYELİK GEREKİYOR</h1>
        
        <p class="vip-message">
            Bu özelliği kullanmak için VIP üye olmanız gerekmektedir. VIP üyelik ile tüm sorgulara erişim sağlayabilirsiniz.
        </p>

        <div class="vip-features">
            <h3><i class="fas fa-star"></i> VIP AVANTAJLARI</h3>
            <div class="feature-item">
                <i class="fas fa-check"></i>
                <span>Tüm Aile Sorguları</span>
            </div>
            <div class="feature-item">
                <i class="fas fa-check"></i>
                <span>GSM-TC Sorguları</span>
            </div>
            <div class="feature-item">
                <i class="fas fa-check"></i>
                <span>Adres Sorguları</span>
            </div>
            <div class="feature-item">
                <i class="fas fa-check"></i>
                <span>IBAN Sorguları</span>
            </div>
            <div class="feature-item">
                <i class="fas fa-check"></i>
                <span>Özel Araçlar</span>
            </div>
            <div class="feature-item">
                <i class="fas fa-check"></i>
                <span>7/24 Öncelikli Destek</span>
            </div>
        </div>

        <div class="vip-contact">
            <h3><i class="fas fa-headset"></i> İLETİŞİM</h3>
            <p class="contact-info">Discord: @tanridiablo</p>
            <p class="contact-info">Telegram: @diablopa</p>
            
            <a href="https://t.me/diablopa" class="telegram-btn" target="_blank">
                <i class="fab fa-telegram"></i> TELEGRAM'DAN YAZIN
            </a>
        </div>

        <a href="/panel" class="back-btn">
            <i class="fas fa-arrow-left"></i> Panele Dön
        </a>
    </div>
</body>
</html>
'''

MAIN_HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diablo System</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: url('https://i.ibb.co/jPbg5kQr/V-D-20251129-121335-350.gif') no-repeat center center fixed;
            background-size: cover;
            color: #fff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .container {
            display: flex;
            flex: 1;
        }

        /* Sidebar Styles */
        .sidebar {
            width: 320px;
            background: rgba(255, 255, 255, 0.1);
            height: 100vh;
            position: fixed;
            left: -320px;
            top: 0;
            transition: left 0.3s ease;
            z-index: 1000;
            overflow-y: auto;
            box-shadow: 2px 0 15px rgba(255, 0, 0, 0.3);
            border-right: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        }

        .sidebar.active {
            left: 0;
        }

        .sidebar-header {
            padding: 20px;
            background: rgba(255, 255, 255, 0.15);
            display: flex;
            align-items: center;
            border-bottom: 2px solid #ff0000;
            backdrop-filter: blur(5px);
        }

        .profile-img {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: 2px solid #ff0000;
            margin-right: 15px;
            object-fit: cover;
        }

        .profile-info {
            display: flex;
            align-items: center;
        }

        .profile-info h3 {
            color: #ff0000;
            font-size: 18px;
            margin-bottom: 5px;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .verified-badge {
            color: #1e90ff;
            font-size: 16px;
            text-shadow: 0 0 10px rgba(30, 144, 255, 0.7);
            animation: pulse-blue 2s infinite;
        }

        @keyframes pulse-blue {
            0% { transform: scale(1); text-shadow: 0 0 5px rgba(30, 144, 255, 0.7); }
            50% { transform: scale(1.1); text-shadow: 0 0 15px rgba(30, 144, 255, 0.9); }
            100% { transform: scale(1); text-shadow: 0 0 5px rgba(30, 144, 255, 0.7); }
        }

        .vip-status {
            background: linear-gradient(45deg, #ffd700, #ffed4e);
            color: #000;
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 12px;
            font-weight: bold;
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.7);
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.7);
        }

        .free-status {
            background: linear-gradient(45deg, #666, #999);
            color: #fff;
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 12px;
            font-weight: bold;
        }

        .profile-info span {
            color: #ff0000;
            font-size: 12px;
            font-weight: bold;
            text-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
        }

        .sidebar-menu {
            padding: 15px 0;
        }

        .menu-title {
            padding: 10px 20px;
            color: #ff0000;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 10px;
            text-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
        }

        .menu-item {
            padding: 12px 20px;
            display: flex;
            align-items: center;
            color: #fff;
            text-decoration: none;
            transition: all 0.3s;
            border-left: 3px solid transparent;
            font-size: 14px;
            position: relative;
            cursor: pointer;
            backdrop-filter: blur(5px);
        }

        .menu-item:hover {
            background: rgba(255, 0, 0, 0.15);
            color: #ff0000;
            border-left: 3px solid #ff0000;
        }

        .menu-item i {
            margin-right: 10px;
            width: 20px;
            text-align: center;
        }

        .menu-item .arrow {
            margin-left: auto;
            transition: transform 0.3s;
        }

        .menu-item.active .arrow {
            transform: rotate(90deg);
        }

        .submenu {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
            background: rgba(255, 255, 255, 0.08);
        }

        .submenu.active {
            max-height: 500px;
        }

        .submenu-item {
            padding: 10px 20px 10px 40px;
            display: flex;
            align-items: center;
            color: #fff;
            text-decoration: none;
            transition: all 0.3s;
            font-size: 13px;
            border-left: 3px solid transparent;
            backdrop-filter: blur(5px);
        }

        .submenu-item:hover {
            background: rgba(255, 0, 0, 0.1);
            color: #ff0000;
            border-left: 3px solid #ff0000;
        }

        .premium-badge {
            background: linear-gradient(45deg, #ff0000, #ff4444);
            color: #fff;
            font-size: 9px;
            padding: 3px 8px;
            border-radius: 12px;
            margin-left: auto;
            font-weight: bold;
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.7);
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
        }

        .free-badge {
            background: linear-gradient(45deg, #00ff00, #44ff44);
            color: #000;
            font-size: 9px;
            padding: 3px 8px;
            border-radius: 12px;
            margin-left: auto;
            font-weight: bold;
        }

        /* Main Content Styles */
        .main-content {
            flex: 1;
            padding: 20px;
            transition: margin-left 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .menu-toggle {
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.15);
            color: #ff0000;
            border: 2px solid #ff0000;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            font-size: 24px;
            cursor: pointer;
            z-index: 999;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.5);
            transition: all 0.3s;
            backdrop-filter: blur(10px);
        }

        .menu-toggle:hover {
            background: rgba(255, 0, 0, 0.2);
            transform: scale(1.1);
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.7);
        }

        .welcome-section {
            max-width: 800px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        }

        .welcome-section h1 {
            font-size: 36px;
            margin-bottom: 20px;
            color: #ff0000;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
        }

        .welcome-section p {
            font-size: 18px;
            line-height: 1.6;
            margin-bottom: 30px;
            color: #fff;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .welcome-icon {
            font-size: 80px;
            color: #ff0000;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
            text-shadow: 0 0 15px rgba(255, 0, 0, 0.7);
        }

        @keyframes pulse {
            0% { transform: scale(1); text-shadow: 0 0 10px rgba(255, 0, 0, 0.7); }
            50% { transform: scale(1.1); text-shadow: 0 0 20px rgba(255, 0, 0, 0.9); }
            100% { transform: scale(1); text-shadow: 0 0 10px rgba(255, 0, 0, 0.7); }
        }

        .vip-promo {
            background: rgba(255, 215, 0, 0.15);
            color: #ffd700;
            padding: 25px;
            border-radius: 12px;
            margin-top: 25px;
            text-align: center;
            border: 1px solid rgba(255, 215, 0, 0.3);
            backdrop-filter: blur(10px);
        }

        .vip-promo h3 {
            margin-bottom: 15px;
            font-size: 22px;
            color: #ffd700;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }

        .vip-promo p {
            color: #ffd700;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 16px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .vip-promo a {
            display: inline-block;
            background: linear-gradient(45deg, #0088cc, #00aced);
            color: white;
            padding: 12px 25px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 15px;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(0, 136, 204, 0.4);
            backdrop-filter: blur(5px);
        }

        .vip-promo a:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 18px rgba(0, 136, 204, 0.6);
        }

        .vip-promo a i {
            margin-right: 8px;
        }

        /* Query Form Styles */
        .query-section {
            display: none;
            width: 100%;
            max-width: 800px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        }

        .query-section.active {
            display: block;
        }

        .query-title {
            font-size: 28px;
            margin-bottom: 25px;
            color: #ff0000;
            text-align: center;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
            position: relative;
            padding-bottom: 10px;
        }

        .query-title:after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 25%;
            width: 50%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #ff0000, transparent);
        }

        .form-group {
            margin-bottom: 25px;
            text-align: left;
        }

        .form-group label {
            display: block;
            margin-bottom: 10px;
            color: #ff0000;
            font-weight: bold;
            font-size: 16px;
            text-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
        }

        .form-control {
            width: 100%;
            padding: 15px;
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            color: #fff;
            font-size: 16px;
            transition: all 0.3s;
            box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(5px);
        }

        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }

        .form-control:focus {
            outline: none;
            border-color: #ff0000;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.5), inset 0 0 10px rgba(0, 0, 0, 0.3);
            background: rgba(255, 255, 255, 0.2);
        }

        textarea.form-control {
            min-height: 120px;
            resize: vertical;
        }

        .btn {
            background: linear-gradient(45deg, #ff0000, #ff4444);
            color: #fff;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.4);
            backdrop-filter: blur(5px);
        }

        .btn:hover {
            background: linear-gradient(45deg, #ff4444, #ff0000);
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(255, 0, 0, 0.6);
        }

        .btn i {
            margin-right: 8px;
        }

        .result-section {
            margin-top: 30px;
            padding: 25px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            display: none;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
        }

        .result-section.active {
            display: block;
        }

        .result-title {
            font-size: 22px;
            margin-bottom: 15px;
            color: #ff0000;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        }

        .result-content {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: monospace;
            text-align: left;
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(5px);
        }

        .back-button {
            margin-top: 20px;
            background: rgba(255, 0, 0, 0.2);
            color: #ff0000;
            border: 1px solid #ff0000;
        }

        .back-button:hover {
            background: rgba(255, 0, 0, 0.3);
        }

        .logout-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 0, 0, 0.2);
            color: #ff0000;
            border: 1px solid #ff0000;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            z-index: 999;
            backdrop-filter: blur(10px);
        }

        .logout-btn:hover {
            background: rgba(255, 0, 0, 0.3);
            transform: translateY(-2px);
        }

        /* EGM İhbar Formu Özel Stiller */
        .egm-form .form-row {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }

        .egm-form .form-row .form-group {
            flex: 1;
            margin-bottom: 0;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                width: 280px;
                left: -280px;
            }

            .welcome-section, .query-section {
                padding: 20px;
            }

            .welcome-section h1 {
                font-size: 28px;
            }

            .welcome-section p {
                font-size: 16px;
            }

            .egm-form .form-row {
                flex-direction: column;
                gap: 0;
            }
        }
    </style>
</head>
<body>
    <!-- Sidebar Menu -->
    <div class="sidebar">
        <div class="sidebar-header">
            <img src="https://i.ibb.co/LddQKGgm/66bedee7a1f3b63b718bf2693dfce196.jpg" alt="DİABLO" class="profile-img">
            <div class="profile-info">
                <div>
                    <h3 id="sidebar-username">DİABLO <i class="fas fa-check-circle verified-badge"></i></h3>
                    <span id="sidebar-status">ÜYE</span>
                </div>
            </div>
        </div>

        <div class="sidebar-menu">
            <!-- AİLE SORGULARI -->
            <div class="menu-title">AİLE SORGULARI</div>
            <div class="menu-item" data-menu="aile">
                <i class="fas fa-users"></i> AİLE SORGULARI <i class="fas fa-chevron-right arrow"></i>
            </div>
            <div class="submenu" id="aile-menu">
                <a href="#" class="submenu-item" data-query="aile">
                    AİLE SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="soyagaci">
                    SOY AĞACI SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="kardes">
                    KARDEŞ SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="cocuk">
                    ÇOCUK SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="es">
                    EŞ SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="sulale">
                    SÜLALE SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
            </div>

            <!-- GSM SORGULARI -->
            <div class="menu-title">GSM SORGULARI</div>
            <div class="menu-item" data-menu="gsm">
                <i class="fas fa-mobile-alt"></i> GSM SORGULARI <i class="fas fa-chevron-right arrow"></i>
            </div>
            <div class="submenu" id="gsm-menu">
                <a href="#" class="submenu-item" data-query="operator">
                    GSM OPERATÖR SORGUSU <span class="free-badge">FREE</span>
                </a>
                <a href="#" class="submenu-item" data-query="gsm-tc">
                    GSM TC SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="tc-gsm">
                    TC GSM SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
            </div>

            <!-- TC SORGULARI -->
            <div class="menu-title">TC SORGULARI</div>
            <div class="menu-item" data-menu="tc">
                <i class="fas fa-id-card"></i> TC SORGULARI <i class="fas fa-chevron-right arrow"></i>
            </div>
            <div class="submenu" id="tc-menu">
                <a href="#" class="submenu-item" data-query="tc">
                    TC SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="tc2">
                    TC SORGUSU 2 <span class="free-badge">FREE</span>
                </a>
                <a href="#" class="submenu-item" data-query="adsoyad">
                    AD SOYAD SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="yas">
                    YAŞ SORGUSU <span class="free-badge">FREE</span>
                </a>
                <a href="#" class="submenu-item" data-query="burc">
                    BURÇ SORGUSU <span class="free-badge">FREE</span>
                </a>
            </div>

            <!-- ADRES SORGULARI -->
            <div class="menu-title">ADRES SORGULARI</div>
            <div class="menu-item" data-menu="adres">
                <i class="fas fa-map-marker-alt"></i> ADRES SORGULARI <i class="fas fa-chevron-right arrow"></i>
            </div>
            <div class="submenu" id="adres-menu">
                <a href="#" class="submenu-item" data-query="adres-api">
                    ADRES SORGUSU <span class="free-badge">FREE</span>
                </a>
                <a href="#" class="submenu-item" data-query="haneadres">
                    HANE ADRES SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
            </div>

            <!-- DİĞER SORGULAR -->
            <div class="menu-title">DİĞER SORGULAR</div>
            <div class="menu-item" data-menu="diger">
                <i class="fas fa-cogs"></i> DİĞER SORGULAR <i class="fas fa-chevron-right arrow"></i>
            </div>
            <div class="submenu" id="diger-menu">
                <a href="#" class="submenu-item" data-query="iban-api">
                    IBAN SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="log">
                    SİTE LOG SORGUSU <span class="premium-badge">PREMIUM</span>
                </a>
                <a href="#" class="submenu-item" data-query="kimlik">
                    KİMLİK ARŞİVİ <span class="premium-badge">PREMIUM</span>
                </a>
            </div>

            <!-- ÖZEL ARAÇLAR -->
            <div class="menu-title">ÖZEL ARAÇLAR</div>
            <a href="#" class="menu-item" data-query="egm">
                <i class="fas fa-exclamation-triangle"></i> EGM İHBAR <span class="premium-badge">PREMIUM</span>
            </a>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content" id="mainContent">
        <button class="menu-toggle" id="menuToggle">
            <i class="fas fa-bars"></i>
        </button>

        <button class="logout-btn" id="logoutBtn">
            <i class="fas fa-sign-out-alt"></i> Çıkış
        </button>

        <!-- Welcome Section -->
        <div class="welcome-section" id="welcome-section">
            <div class="welcome-icon">
                <i class="fas fa-fire"></i>
            </div>
            <h1>DİABLO SYSTEM'E HOŞGELDİN</h1>
            <p>SOL ÜSTTEKİ MENÜDEN SORGU SEÇENEKLERİNE ERİŞEBİLİRSİN İYİ SORGULAR.</p>
            
            <div class="vip-promo">
                <h3><i class="fas fa-crown"></i> VIP SATIN AL</h3>
                <p>Discord: @tanridiablo</p>
                <p>Telegram: @diablopa</p>
                <a href="https://t.me/diablopa" target="_blank">
                    <i class="fab fa-telegram"></i> VIP Satın Almak İçin Tıkla
                </a>
            </div>
        </div>

        <!-- Query Sections -->
        <div class="query-section" id="query-section">
            <h2 class="query-title" id="query-title">Sorgu Başlığı</h2>

            <form id="query-form">
                <div class="form-group" id="input-fields">
                    <!-- Input fields will be dynamically added here -->
                </div>

                <button type="submit" class="btn">
                    <i class="fas fa-search"></i> Sorgula
                </button>
            </form>

            <div class="result-section" id="result-section">
                <h3 class="result-title">Sorgu Sonucu</h3>
                <div class="result-content" id="result-content">
                    <!-- Results will be displayed here -->
                </div>
                <button class="btn back-button" id="back-button">
                    <i class="fas fa-arrow-left"></i> Geri Dön
                </button>
            </div>
        </div>
    </div>

    <script>
        // Kullanıcı bilgilerini yükle
        const token = localStorage.getItem('token');
        const userType = localStorage.getItem('user_type');
        const vipStatus = localStorage.getItem('vip_status') === '1';
        const username = localStorage.getItem('username') || 'Kullanıcı';

        // Token kontrolü
        if (!token) {
            window.location.href = '/';
        }

        // Sidebar bilgilerini güncelle
        document.getElementById('sidebar-username').innerHTML = `${username} <i class="fas fa-check-circle verified-badge"></i>`;
        document.getElementById('sidebar-status').textContent = vipStatus ? 'VIP ÜYE' : 'ÜCRETSİZ ÜYE';

        // Menu Toggle
        const menuToggle = document.querySelector('.menu-toggle');
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');

        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && !sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });

        // Submenu Toggle
        document.querySelectorAll('.menu-item[data-menu]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const menuId = item.getAttribute('data-menu');
                const submenu = document.getElementById(`${menuId}-menu`);

                // Close other submenus
                document.querySelectorAll('.submenu').forEach(sm => {
                    if (sm !== submenu) {
                        sm.classList.remove('active');
                    }
                });

                // Remove active class from other menu items
                document.querySelectorAll('.menu-item[data-menu]').forEach(mi => {
                    if (mi !== item) {
                        mi.classList.remove('active');
                    }
                });

                // Toggle current submenu
                submenu.classList.toggle('active');
                item.classList.toggle('active');
            });
        });

        // Query Handling
        const welcomeSection = document.getElementById('welcome-section');
        const querySection = document.getElementById('query-section');
        const queryTitle = document.getElementById('query-title');
        const inputFields = document.getElementById('input-fields');
        const queryForm = document.getElementById('query-form');
        const resultSection = document.getElementById('result-section');
        const resultContent = document.getElementById('result-content');
        const backButton = document.getElementById('back-button');

        // Free queries
        const freeQueries = ['operator', 'yas', 'burc', 'tc2', 'adres-api'];

        // Query titles
        const queryTitles = {
            'soyagaci': 'SOY AĞACI SORGUSU',
            'log': 'SİTE LOG SORGUSU',
            'kardes': 'KARDEŞ SORGUSU',
            'cocuk': 'ÇOCUK SORGUSU',
            'es': 'EŞ SORGUSU',
            'iban-api': 'IBAN SORGUSU',
            'yas': 'YAŞ SORGUSU',
            'sulale': 'SÜLALE SORGUSU',
            'burc': 'BURÇ SORGUSU',
            'tc2': 'TC SORGUSU 2',
            'haneadres': 'HANE ADRES SORGUSU',
            'adres-api': 'ADRES SORGUSU',
            'operator': 'GSM OPERATÖR SORGUSU',
            'aile': 'AİLE SORGUSU',
            'tc': 'TC SORGUSU',
            'adsoyad': 'AD SOYAD SORGUSU',
            'egm': 'EGM İHBAR SİSTEMİ',
            'kimlik': 'KİMLİK ARŞİVİ SORGUSU',
            'gsm-tc': 'GSM TC SORGUSU',
            'tc-gsm': 'TC GSM SORGUSU'
        };

        // Menu item click handlers
        document.querySelectorAll('.menu-item, .submenu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const queryType = item.getAttribute('data-query');

                if (queryType) {
                    // Close sidebar on mobile
                    if (window.innerWidth <= 768) {
                        sidebar.classList.remove('active');
                    }

                    // VIP kontrolü - VIP değilse ve ücretsiz sorgu değilse
                    if (!freeQueries.includes(queryType) && !vipStatus && userType !== 'admin') {
                        // VIP promo sayfasına yönlendir
                        window.open('/vip-promo', '_blank');
                        return;
                    }

                    // Hide welcome section and show query section
                    welcomeSection.style.display = 'none';
                    querySection.classList.add('active');

                    // Set query title
                    queryTitle.textContent = queryTitles[queryType] || 'Sorgu';

                    // Clear previous input fields
                    inputFields.innerHTML = '';

                    // Special handling for EGM İhbar
                    if (queryType === 'egm') {
                        createEgmForm();
                        queryForm.setAttribute('data-query-type', 'egm');
                    } else {
                        // Create input fields based on query type
                        createInputFields(queryType);
                        queryForm.setAttribute('data-query-type', queryType);
                    }

                    // Hide result section
                    resultSection.classList.remove('active');
                }
            });
        });

        // Create input fields for query
        function createInputFields(queryType) {
            const inputConfigs = {
                'soyagaci': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'log': [{name: 'site', label: 'Site Adresi', placeholder: 'Site adresi girin'}],
                'kardes': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'cocuk': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'es': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'iban-api': [{name: 'iban', label: 'IBAN No', placeholder: 'IBAN No girin'}],
                'yas': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'sulale': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'burc': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'tc2': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'haneadres': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'adres-api': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'operator': [{name: 'numara', label: 'Telefon Numarası', placeholder: 'Telefon numarası girin'}],
                'aile': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'tc': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'adsoyad': [
                    {name: 'ad', label: 'Ad', placeholder: 'Ad girin'},
                    {name: 'soyad', label: 'Soyad', placeholder: 'Soyad girin'},
                    {name: 'il', label: 'İl', placeholder: 'İl girin'},
                    {name: 'ilce', label: 'İlçe', placeholder: 'İlçe girin'}
                ],
                'gsm-tc': [{name: 'gsm', label: 'GSM Numarası', placeholder: 'GSM numarası girin'}],
                'tc-gsm': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}],
                'kimlik': [{name: 'tc', label: 'TC Kimlik No', placeholder: 'TC Kimlik No girin'}]
            };

            const config = inputConfigs[queryType] || [{name: 'input', label: 'Giriş', placeholder: 'Değer girin'}];

            config.forEach(field => {
                const div = document.createElement('div');
                div.className = 'form-group';

                const label = document.createElement('label');
                label.textContent = field.label;
                label.setAttribute('for', field.name);

                const input = document.createElement('input');
                input.type = 'text';
                input.id = field.name;
                input.name = field.name;
                input.className = 'form-control';
                input.placeholder = field.placeholder;

                div.appendChild(label);
                div.appendChild(input);
                inputFields.appendChild(div);
            });
        }

        // Create EGM İhbar Form
        function createEgmForm() {
            inputFields.innerHTML = '';
            inputFields.className = 'egm-form';

            // Şahıs Bilgileri
            const personSection = document.createElement('div');
            personSection.innerHTML = '<h3 style="color:#ff0000; margin-bottom:15px; text-shadow:0 0 5px rgba(255,0,0,0.5); border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:5px;">Şahıs Bilgileri</h3>';
            inputFields.appendChild(personSection);

            const row1 = document.createElement('div');
            row1.className = 'form-row';

            const tcDiv = document.createElement('div');
            tcDiv.className = 'form-group';
            tcDiv.innerHTML = `
                <label for="tc">TC Kimlik No</label>
                <input type="text" id="tc" name="tc" class="form-control" placeholder=" TC Kimlik No girin" maxlength="11">
            `;

            const adDiv = document.createElement('div');
            adDiv.className = 'form-group';
            adDiv.innerHTML = `
                <label for="ad">Ad</label>
                <input type="text" id="ad" name="ad" class="form-control" placeholder=" Ad girin">
            `;

            row1.appendChild(tcDiv);
            row1.appendChild(adDiv);
            inputFields.appendChild(row1);

            const row2 = document.createElement('div');
            row2.className = 'form-row';

            const soyadDiv = document.createElement('div');
            soyadDiv.className = 'form-group';
            soyadDiv.innerHTML = `
                <label for="soyad">Soyad</label>
                <input type="text" id="soyad" name="soyad" class="form-control" placeholder=" Soyad girin">
            `;

            const telefonDiv = document.createElement('div');
            telefonDiv.className = 'form-group';
            telefonDiv.innerHTML = `
                <label for="telefon">Telefon</label>
                <input type="text" id="telefon" name="telefon" class="form-control" placeholder=" Telefon girin">
            `;

            row2.appendChild(soyadDiv);
            row2.appendChild(telefonDiv);
            inputFields.appendChild(row2);

            // İhbar Detayları
            const ihbarSection = document.createElement('div');
            ihbarSection.innerHTML = '<h3 style="color:#ff0000; margin:20px 0 15px; text-shadow:0 0 5px rgba(255,0,0,0.5); border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:5px;">İhbar Detayları</h3>';
            inputFields.appendChild(ihbarSection);

            const ihbarDiv = document.createElement('div');
            ihbarDiv.className = 'form-group';
            ihbarDiv.innerHTML = `
                <label for="ihbar">İhbar Detayları</label>
                <textarea id="ihbar" name="ihbar" class="form-control" placeholder=" İhbar detaylarını yazın..."></textarea>
            `;
            inputFields.appendChild(ihbarDiv);

            const adresDiv = document.createElement('div');
            adresDiv.className = 'form-group';
            adresDiv.innerHTML = `
                <label for="adres">Adres</label>
                <textarea id="adres" name="adres" class="form-control" placeholder=" Adres bilgilerini yazın..."></textarea>
            `;
            inputFields.appendChild(adresDiv);
        }

        // Form submission
        queryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const queryType = queryForm.getAttribute('data-query-type');

            if (queryType === 'egm') {
                // EGM İhbar işleme
                const tc = document.querySelector('[name="tc"]').value;
                const ad = document.querySelector('[name="ad"]').value;
                const soyad = document.querySelector('[name="soyad"]').value;
                const telefon = document.querySelector('[name="telefon"]').value;
                const ihbar = document.querySelector('[name="ihbar"]').value;
                const adres = document.querySelector('[name="adres"]').value;

                if (!tc || !ad || !soyad || !ihbar) {
                    alert('Lütfen zorunlu alanları doldurun!');
                    return;
                }

                // İhbar oluştur
                const ihbarRaporu = `
EGM İHBAR RAPORU
================
Tarih: ${new Date().toLocaleString('tr-TR')}

ŞAHIS BİLGİLERİ:
----------------
TC Kimlik: ${tc}
Ad: ${ad}
Soyad: ${soyad}
Telefon: ${telefon || 'Belirtilmemiş'}

ADRES:
------
${adres || 'Belirtilmemiş'}

İHBAR DETAYLARI:
----------------
${ihbar}

İhbar sisteme kaydedilmiştir.
İhbar No: ${Math.floor(100000 + Math.random() * 900000)}
                `;

                resultContent.textContent = ihbarRaporu;
                resultSection.classList.add('active');

            } else {
                // API sorgusu
                const formData = new FormData(queryForm);
                const queryData = {};
                formData.forEach((value, key) => {
                    queryData[key] = value;
                });

                // Show loading state
                resultContent.textContent = 'Sorgu yapılıyor...';
                resultSection.classList.add('active');

                // Make API request
                fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': token
                    },
                    body: JSON.stringify({
                        query_type: queryType,
                        query_data: queryData
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        resultContent.textContent = data.result || 'Sonuç bulunamadı.';
                    } else {
                        resultContent.textContent = 'Hata: ' + data.message;
                    }
                })
                .catch(error => {
                    resultContent.textContent = 'Sorgu sırasında hata oluştu: ' + error.message;
                });
            }
        });

        // Back button
        backButton.addEventListener('click', () => {
            resultSection.classList.remove('active');
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            localStorage.clear();
            window.location.href = '/';
        });
    </script>
</body>
</html>
'''

# Admin HTML de cam efekti eklendi (kısaltılmış)
ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diablo System - Admin Panel</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: url('https://i.ibb.co/jPbg5kQr/V-D-20251129-121335-350.gif') no-repeat center center fixed;
            background-size: cover;
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }

        .admin-container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .admin-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.3);
            backdrop-filter: blur(15px);
        }

        .admin-header h1 {
            color: #ff0000;
            font-size: 36px;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
        }

        .admin-header p {
            color: #fff;
            font-size: 16px;
            text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
        }

        .admin-nav {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .nav-btn {
            background: rgba(255, 255, 255, 0.15);
            color: #ff0000;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            backdrop-filter: blur(10px);
        }

        .nav-btn:hover, .nav-btn.active {
            background: rgba(255, 0, 0, 0.3);
            transform: translateY(-2px);
        }

        .admin-section {
            display: none;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 20px;
            backdrop-filter: blur(15px);
        }

        /* ... Diğer admin stilleri cam efekti ile güncellendi ... */
    </style>
</head>
<body>
    <!-- Admin HTML içeriği aynı kaldı, sadece stiller güncellendi -->
</body>
</html>
'''

# Veritabanı başlatma ve diğer backend kodları aynı kaldı...
# (Yukarıdaki backend kodunun tamamını buraya ekleyin)
# Veritabanı başlatma
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Kullanıcılar tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  user_type TEXT NOT NULL DEFAULT 'user',
                  vip_status INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Varsayılan kullanıcılar
    try:
        # Admin kullanıcı
        admin_password = hashlib.sha256('00000000'.encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password, user_type, vip_status) VALUES (?, ?, ?, ?)",
                  ('admin', admin_password, 'admin', 1))

        # Örnek kullanıcı
        user_password = hashlib.sha256('123456'.encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password, user_type, vip_status) VALUES (?, ?, ?, ?)",
                  ('testuser', user_password, 'user', 0))
    except:
        pass

    conn.commit()
    conn.close()

init_db()

# Token doğrulama decorator'ı
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = get_user_by_username(data['username'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Admin yetkisi kontrolü
def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user['user_type'] != 'admin':
            return jsonify({'message': 'Admin access required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# Kullanıcıyı kullanıcı adına göre getirme
def get_user_by_username(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        return {
            'id': user[0],
            'username': user[1],
            'password': user[2],
            'user_type': user[3],
            'vip_status': user[4]
        }
    return None

# Güvenlik middleware
@app.before_request
def security_checks():
    client_ip = get_client_ip()

    # Rate limiting
    if not check_rate_limit(client_ip):
        return jsonify({'success': False, 'message': 'Çok fazla istek gönderdiniz. Lütfen bekleyin.'}), 429

    # SQL injection ve XSS koruması
    if request.method in ['POST', 'PUT']:
        if request.is_json:
            data = request.get_json()
            for key, value in data.items():
                if isinstance(value, str):
                    try:
                        sanitized = sanitize_input(value)
                        data[key] = sanitized
                    except ValueError as e:
                        return jsonify({'success': False, 'message': str(e)}), 400
        else:
            for key, value in request.form.items():
                if isinstance(value, str):
                    try:
                        sanitized = sanitize_input(value)
                        request.form[key] = sanitized
                    except ValueError as e:
                        return jsonify({'success': False, 'message': str(e)}), 400

# API Endpoint'leri
@app.route('/')
def login_page():
    return render_template_string(LOGIN_HTML)

@app.route('/panel')
def panel_page():
    return render_template_string(MAIN_HTML)

@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/vip-promo')
def vip_promo_page():
    return render_template_string(VIP_PROMO_HTML)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Input sanitization
    try:
        username = sanitize_input(username) if username else None
        password = sanitize_input(password) if password else None
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})

    if not username or not password:
        return jsonify({'success': False, 'message': 'Kullanıcı adı ve şifre gereklidir!'})

    # Admin free giriş kontrolü
    if username == 'admin' and password == '00000000':
        token = jwt.encode({
            'username': 'admin',
            'user_type': 'admin',
            'vip_status': 1,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'])

        return jsonify({
            'success': True,
            'message': 'Admin girişi başarılı!',
            'token': token,
            'user_type': 'admin',
            'vip_status': 1,
            'username': 'admin'
        })

    # Normal kullanıcı girişi
    user = get_user_by_username(username)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if user and user['password'] == hashed_password:
        token = jwt.encode({
            'username': user['username'],
            'user_type': user['user_type'],
            'vip_status': user['vip_status'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'])

        return jsonify({
            'success': True,
            'message': 'Giriş başarılı!',
            'token': token,
            'user_type': user['user_type'],
            'vip_status': user['vip_status'],
            'username': user['username']
        })

    return jsonify({'success': False, 'message': 'Geçersiz kullanıcı adı veya şifre!'})

# Ücretsiz sorgular
FREE_QUERIES = ['operator', 'yas', 'burc', 'tc2', 'adres-api']

@app.route('/api/query', methods=['POST'])
@token_required
def make_query(current_user):
    data = request.get_json()
    query_type = data.get('query_type')
    query_data = data.get('query_data')

    # Input sanitization for query data
    if query_data:
        for key, value in query_data.items():
            if isinstance(value, str):
                try:
                    query_data[key] = sanitize_input(value)
                except ValueError as e:
                    return jsonify({'success': False, 'message': str(e)})

    # VIP kontrolü (ücretsiz sorgular hariç)
    if query_type not in FREE_QUERIES and not current_user['vip_status'] and current_user['user_type'] != 'admin':
        return jsonify({'success': False, 'message': 'Bu sorgu için VIP üyelik gereklidir!'})

    # Sorgu işleme
    try:
        result = process_query(query_type, query_data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Sorgu sırasında hata: {str(e)}'})

def process_query(query_type, query_data):
    # API endpoint'leri
    endpoints = {
        'soyagaci': 'https://dosya.alwaysdata.net/api/soyagaci.php',
        'log': 'https://dosya.alwaysdata.net/api/log.php',
        'kardes': 'https://dosya.alwaysdata.net/api/kardes.php',
        'cocuk': 'https://dosya.alwaysdata.net/api/cocuk.php',
        'es': 'https://dosya.alwaysdata.net/api/es.php',
        'iban-api': 'https://dosya.alwaysdata.net/api/iban.php',
        'yas': 'https://dosya.alwaysdata.net/api/yas.php',
        'sulale': 'https://dosya.alwaysdata.net/api/sulale.php',
        'burc': 'https://dosya.alwaysdata.net/api/burc.php',
        'tc2': 'https://dosya.alwaysdata.net/api/tc2.php',
        'haneadres': 'https://dosya.alwaysdata.net/api/haneadres.php',
        'adres-api': 'https://dosya.alwaysdata.net/api/adres.php',
        'operator': 'https://dosya.alwaysdata.net/api/gncloperator.php',
        'aile': 'https://dosya.alwaysdata.net/api/aile.php',
        'tc': 'https://dosya.alwaysdata.net/api/tc.php',
        'adsoyad': 'https://dosya.alwaysdata.net/api/adsoyad.php',
        'gsm-tc': 'https://dosya.alwaysdata.net/api/gsmtc.php',
        'tc-gsm': 'https://dosya.alwaysdata.net/api/tcgsm.php',
        'kimlik': 'https://dosya.alwaysdata.net/api/tc.php'  # Geçici olarak TC sorgusuna yönlendiriyoruz
    }

    if query_type not in endpoints:
        return "Geçersiz sorgu türü!"

    # API isteği
    response = requests.get(endpoints[query_type], params=query_data, timeout=30)
    return response.text

# Admin endpoint'leri
@app.route('/api/admin/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username, user_type, vip_status, created_at FROM users")
    users = c.fetchall()
    conn.close()

    user_list = []
    for user in users:
        user_list.append({
            'id': user[0],
            'username': user[1],
            'user_type': user[2],
            'vip_status': user[3],
            'created_at': user[4]
        })

    return jsonify({'success': True, 'users': user_list})

@app.route('/api/admin/create_user', methods=['POST'])
@token_required
@admin_required
def create_user(current_user):
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type', 'user')
    vip_status = data.get('vip_status', 0)

    # Input sanitization
    try:
        username = sanitize_input(username) if username else None
        password = sanitize_input(password) if password else None
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})

    if not username or not password:
        return jsonify({'success': False, 'message': 'Kullanıcı adı ve şifre gereklidir!'})

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (username, password, user_type, vip_status) VALUES (?, ?, ?, ?)",
                  (username, hashed_password, user_type, vip_status))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Kullanıcı başarıyla oluşturuldu!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Bu kullanıcı adı zaten kullanılıyor!'})

@app.route('/api/admin/update_vip', methods=['POST'])
@token_required
@admin_required
def update_vip_status(current_user):
    data = request.get_json()
    user_id = data.get('user_id')
    vip_status = data.get('vip_status')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET vip_status = ? WHERE id = ?", (vip_status, user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'VIP durumu güncellendi!'})

@app.route('/api/admin/delete_user', methods=['POST'])
@token_required
@admin_required
def delete_user(current_user):
    data = request.get_json()
    user_id = data.get('user_id')

  
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT user_type FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()

    if user and user[0] == 'admin':
        conn.close()
        return jsonify({'success': False, 'message': 'Admin kullanıcı silinemez!'})

    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Kullanıcı başarıyla silindi!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# Cài skill topik-exam-upload trên Windows và lưu TOPIK_API_URL, TOPIK_API_TOKEN
# vào biến môi trường của tài khoản người dùng (còn nguyên sau khi khởi động lại).
# Chạy: bấm đúp install.cmd, hoặc: powershell -ExecutionPolicy Bypass -File install.ps1 [-Agent claude|codex|both]
param([ValidateSet('claude', 'codex', 'both')][string]$Agent)
$ErrorActionPreference = 'Stop'

$skill = Join-Path $PSScriptRoot 'skills\topik-exam-upload'
if (-not (Test-Path $skill)) { throw "Không thấy thư mục skill: $skill" }

if (-not $Agent) {
    Write-Host 'Cài cho agent nào?'
    Write-Host '  1. Claude Code'
    Write-Host '  2. Codex'
    Write-Host '  3. Cả hai'
    $Agent = @{ '1' = 'claude'; '2' = 'codex'; '3' = 'both' }[(Read-Host 'Chọn 1, 2 hoặc 3')]
    if (-not $Agent) { throw 'Lựa chọn không hợp lệ.' }
}

$targets = @()
if ($Agent -in 'claude', 'both') { $targets += Join-Path $HOME '.claude\skills' }
if ($Agent -in 'codex', 'both') { $targets += Join-Path $HOME '.agents\skills' }

foreach ($dir in $targets) {
    $dest = Join-Path $dir 'topik-exam-upload'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }  # thay bản cũ bằng bản mới
    Copy-Item -Recurse $skill $dest
    Write-Host "Đã chép skill vào $dest"
}

$oldUrl = [Environment]::GetEnvironmentVariable('TOPIK_API_URL', 'User')
$prompt = 'Địa chỉ API (vd https://api.example.com)'
if ($oldUrl) { $prompt += " [Enter để giữ $oldUrl]" }
$url = (Read-Host $prompt).Trim().TrimEnd('/')
if (-not $url) { $url = $oldUrl }
if ($url -notmatch '^https?://') { throw 'Địa chỉ API phải bắt đầu bằng http:// hoặc https://' }

$secure = Read-Host 'Token API (tpk_..., không hiện khi gõ; Enter để giữ token cũ)' -AsSecureString
$token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)).Trim()
if (-not $token) { $token = [Environment]::GetEnvironmentVariable('TOPIK_API_TOKEN', 'User') }
if (-not $token) { throw 'Chưa có token.' }

# Phạm vi User: lưu trong registry của tài khoản, không cần quyền admin.
[Environment]::SetEnvironmentVariable('TOPIK_API_URL', $url, 'User')
[Environment]::SetEnvironmentVariable('TOPIK_API_TOKEN', $token, 'User')
Write-Host 'Đã lưu TOPIK_API_URL và TOPIK_API_TOKEN cho tài khoản này.'

if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Warning 'Không thấy lệnh python3. Skill gọi python3: cài Python 3.10+ (python.org hoặc Microsoft Store) rồi kiểm tra lại bằng: python3 --version'
}

Write-Host ''
Write-Host 'Xong. Đóng hẳn rồi mở lại terminal và ứng dụng Claude/Codex để chúng nhận biến mới.'

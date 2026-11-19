# Cài skill topik-exam-upload trên Windows và lưu TOPIK_API_URL, TOPIK_API_TOKEN
# vào biến môi trường của tài khoản người dùng (còn nguyên sau khi khởi động lại).
# Chạy từ GitHub (trong PowerShell): iex ((irm https://raw.githubusercontent.com/Artteiv/topik-editor-skills/main/install.ps1) -replace '^\uFEFF')
# Chạy trong repo: bấm đúp install.cmd, hoặc: powershell -ExecutionPolicy Bypass -File install.ps1 [-Agent claude|codex|both]
param([ValidateSet('claude', 'codex', 'both')][string]$Agent)
$ErrorActionPreference = 'Stop'

$skill = if ($PSScriptRoot) { Join-Path $PSScriptRoot 'skills\topik-exam-upload' } else { '' }
if (-not $skill -or -not (Test-Path $skill)) {
    # Chạy từ GitHub (lệnh iex ở trên): không có repo cạnh script, tải bản mới nhất của main.
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ("topik-skill-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $tmp | Out-Null
    Write-Host 'Đang tải skill từ GitHub...'
    Invoke-WebRequest -UseBasicParsing 'https://codeload.github.com/Artteiv/topik-editor-skills/zip/main' -OutFile "$tmp\repo.zip"
    Expand-Archive "$tmp\repo.zip" $tmp
    $skill = "$tmp\topik-editor-skills-main\skills\topik-exam-upload"
    if (-not (Test-Path $skill)) { throw 'Tải về không thấy thư mục skill.' }
}

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

# Chạy thử thay vì Get-Command: Windows có sẵn python3.exe giả (mở Store) khi chưa cài Python.
function Test-Python {
    try { & python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>$null; return $LASTEXITCODE -eq 0 } catch { return $false }
}
if (-not (Test-Python)) {
    Write-Host 'Chưa có python3 bản 3.10 trở lên (skill cần lệnh này).'
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Warning 'Không có winget. Cài Python 3.12 từ Microsoft Store (bản Store có lệnh python3), rồi chạy: python3 --version'
    } elseif ((Read-Host 'Cài Python 3.12 từ Microsoft Store bằng winget? (Y/n)') -notmatch '^[nN]') {
        # Bản Store có lệnh python3; bản python.org chỉ có python và py.
        winget install --id 9NCVDN91XZQP -e --source msstore --accept-package-agreements --accept-source-agreements
        if (Test-Python) { Write-Host 'Đã cài Python.' } else { Write-Warning 'Cài xong nhưng chưa gọi được python3. Mở terminal mới rồi chạy: python3 --version' }
    }
}

Write-Host ''
Write-Host 'Xong. Đóng hẳn rồi mở lại terminal và ứng dụng Claude/Codex để chúng nhận biến mới.'

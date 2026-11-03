; ==============================================================================
; CaRI-Siber ID - NSIS Installer Script
; Cognitive Domain Intelligence & Narrative Threat Monitoring Platform
; ==============================================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"

; --- Informasi Produk ---
!define PRODUCT_NAME "CaRI-Siber ID"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "CaRI-Siber ID Team"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\CaRI-Siber-ID.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "dist\CaRI-Siber-ID-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\CaRI-Siber ID"
InstallDirRegKey HKCU "${PRODUCT_DIR_REGKEY}" ""
RequestExecutionLevel user
Unicode True
SetCompressor /SOLID lzma

; --- Pengaturan Antarmuka Modern (MUI2) ---
!define MUI_ABORTWARNING
!define MUI_ICON "resources\icon.ico"
!define MUI_UNICON "resources\icon.ico"

; --- Halaman Installer ---
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Halaman Selesai dengan opsi langsung menjalankan aplikasi
!define MUI_FINISHPAGE_RUN "$INSTDIR\CaRI-Siber-ID.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Jalankan ${PRODUCT_NAME} sekarang"
!insertmacro MUI_PAGE_FINISH

; --- Halaman Uninstaller ---
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; --- Bahasa ---
!insertmacro MUI_LANGUAGE "Indonesian"
!insertmacro MUI_LANGUAGE "English"

; --- Bagian Instalasi Utama ---
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite on

    ; Salin seluruh direktori hasil build PyInstaller
    File /r "dist\CaRI-Siber-ID\*.*"

    ; Buat Uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Pintasan Menu Mulai (Start Menu)
    CreateDirectory "$SMPROGRAMS\CaRI-Siber ID"
    CreateShortcut "$SMPROGRAMS\CaRI-Siber ID\CaRI-Siber ID.lnk" "$INSTDIR\CaRI-Siber-ID.exe"
    CreateShortcut "$SMPROGRAMS\CaRI-Siber ID\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

    ; Pintasan Desktop
    CreateShortcut "$DESKTOP\CaRI-Siber ID.lnk" "$INSTDIR\CaRI-Siber-ID.exe"

    ; Registrasi di Windows Apps & Features (Add/Remove Programs)
    WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\CaRI-Siber-ID.exe"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME} - Cognitive Domain Intelligence"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\CaRI-Siber-ID.exe"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

; --- Bagian Uninstall ---
Section "Uninstall"
    ; Hapus pintasan
    Delete "$DESKTOP\CaRI-Siber ID.lnk"
    Delete "$SMPROGRAMS\CaRI-Siber ID\CaRI-Siber ID.lnk"
    Delete "$SMPROGRAMS\CaRI-Siber ID\Uninstall.lnk"
    RMDir "$SMPROGRAMS\CaRI-Siber ID"

    ; Hapus berkas instalasi
    RMDir /r "$INSTDIR"

    ; Hapus registry
    DeleteRegKey HKCU "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKCU "${PRODUCT_DIR_REGKEY}"

    SetAutoClose true
SectionEnd

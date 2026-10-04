; Instalador de Perfúmappte (Inno Setup 6). No se compila a mano: usa  python -m tools.build_installer
;   /DAppVersion=1.0.0   versión
;   /DSourceDir=...      carpeta generada por PyInstaller (dist\Perfumappte)
;   /DSeedDb=...         (opcional) base de datos inicial limpia que se instala la primera vez
;
; El asistente tiene dos páginas opcionales propias:
;   · Kaggle  -> copia kaggle.json (o access_token) a %USERPROFILE%\.kaggle para poder actualizar la base de datos de perfumes.
;   · Gemini  -> guarda la clave de la IA de Góngora en la carpeta de datos del usuario (gemini.key).
; Instalación desatendida (/VERYSILENT) con esos datos:  /GEMINIKEY=...  /KAGGLEFILE=ruta\kaggle.json
; Con /DSeedDb la base de datos de perfumes va incluida y Kaggle es opcional; sin ella, Kaggle es OBLIGATORIO para descargarla.
; La actualización desde la app lanza este mismo instalador con  /SILENT /RELAUNCH=1  (conserva tus datos y vuelve a abrir la app).
; Solo para pruebas:  /DATADIR=ruta  /KAGGLEDIR=ruta  (para no tocar tus carpetas reales)

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\build\dist\Perfumappte"
#endif
#ifdef SeedDb
  #define FileSuffix "-con-base-de-datos"
#else
  #define FileSuffix ""
#endif
#define AppName "Perfúmappte"
#define AppExe "Perfumappte.exe"

[Setup]
AppId={{B7F3C6A2-5D41-4E8B-9C2F-6A1D7E3F9B10}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppName}
DefaultDirName={autopf}\Perfumappte
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=Perfumappte-Setup-{#AppVersion}{#FileSuffix}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern
WizardSizePercent=120,130
Compression=lzma2/ultra64
SolidCompression=yes
CloseApplications=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
spanish.DesktopIcon=Crear un icono en el escritorio
english.DesktopIcon=Create a desktop icon
; --- página de Kaggle
spanish.KaggleTitle=Actualizar la base de datos de perfumes (opcional)
spanish.KaggleDesc=Perfúmappte ya incluye una base de datos lista para usar.
spanish.KaggleBody=Si quieres poder ACTUALIZARLA con los perfumes nuevos, necesitas una cuenta gratuita de Kaggle:%n%n  1. Entra en kaggle.com (crea una cuenta o inicia sesión).%n  2. Ve a Settings > API  (kaggle.com/settings/api).%n  3. En el apartado API pulsa «Create Legacy API Key»: es la ÚNICA opción que descarga el archivo kaggle.json.%n  4. Selecciona ese archivo aquí abajo: el instalador lo guardará por ti en  %1  (la carpeta .kaggle de tu usuario).%n%nEs OPCIONAL. Si lo dejas vacío, la base de datos de perfumes NO se actualizará: seguirás usando la que viene incluida. Podrás hacerlo más tarde copiando el archivo a esa misma carpeta.
spanish.KaggleBodyNoDb=Esta versión NO incluye la base de datos de perfumes: se descarga de Kaggle (gratis). Para ello necesitas una cuenta de Kaggle:%n%n  1. Entra en kaggle.com (crea una cuenta o inicia sesión).%n  2. Ve a Settings > API  (kaggle.com/settings/api).%n  3. En el apartado API pulsa «Create Legacy API Key»: es la ÚNICA opción que descarga el archivo kaggle.json.%n  4. Selecciona ese archivo aquí abajo: el instalador lo guardará por ti en  %1  (la carpeta .kaggle de tu usuario).%n%nEs NECESARIO: sin este archivo la aplicación no tendrá perfumes que mostrar.
spanish.KaggleTitleNoDb=Descargar la base de datos de perfumes (necesario)
spanish.KaggleDescNoDb=Perfúmappte descarga la base de datos de perfumes de Kaggle.
spanish.KaggleFileRequired=Archivo kaggle.json:
spanish.KaggleRequired=Necesitas indicar el archivo kaggle.json para que la aplicación pueda descargar la base de datos de perfumes.%n%nSi todavía no lo tienes, pulsa «Abrir kaggle.com/settings/api», crea la clave con «Create Legacy API Key» y vuelve aquí.
spanish.KaggleOpen=Abrir kaggle.com/settings/api
spanish.KaggleFile=Archivo kaggle.json (opcional):
spanish.KaggleBrowse=Examinar...
spanish.KaggleFilter=Credenciales de Kaggle (kaggle.json)|kaggle.json|Todos los archivos (*.*)|*.*
spanish.KaggleInvalid=Ese archivo no parece un kaggle.json válido (debe contener "username" y "key"). Elige el archivo que descargaste de Kaggle con «Create Legacy API Key» o, si es opcional, deja el campo vacío.
spanish.KaggleExists=Ya tienes credenciales de Kaggle guardadas en %1.%n%n¿Quieres reemplazarlas por el archivo elegido?
spanish.KaggleEmptyWarn=No has indicado el archivo de Kaggle.%n%nLa base de datos de perfumes NO se actualizará (seguirás con la que viene incluida). Podrás añadirlo más tarde copiando kaggle.json a la carpeta  %1.%n%n¿Continuar sin él?
english.KaggleTitle=Update the perfume database (optional)
english.KaggleDesc=Perfúmappte already includes a ready-to-use perfume database.
english.KaggleBody=If you want to be able to UPDATE it with new perfumes, you need a free Kaggle account:%n%n  1. Go to kaggle.com (sign up or sign in).%n  2. Open Settings > API  (kaggle.com/settings/api).%n  3. In the API section click "Create Legacy API Key": it is the ONLY option that downloads the kaggle.json file.%n  4. Select that file below: the installer will save it for you in  %1  (the .kaggle folder of your user).%n%nIt is OPTIONAL. If you leave it empty, the perfume database will NOT be updated: you will keep using the bundled one. You can do it later by copying the file to that same folder.
english.KaggleBodyNoDb=This version does NOT include the perfume database: it is downloaded from Kaggle (free). For that you need a Kaggle account:%n%n  1. Go to kaggle.com (sign up or sign in).%n  2. Open Settings > API  (kaggle.com/settings/api).%n  3. In the API section click "Create Legacy API Key": it is the ONLY option that downloads the kaggle.json file.%n  4. Select that file below: the installer will save it for you in  %1  (the .kaggle folder of your user).%n%nIt is REQUIRED: without this file the application will have no perfumes to show.
english.KaggleTitleNoDb=Download the perfume database (required)
english.KaggleDescNoDb=Perfúmappte downloads the perfume database from Kaggle.
english.KaggleFileRequired=kaggle.json file:
english.KaggleRequired=You need to select the kaggle.json file so the application can download the perfume database.%n%nIf you do not have it yet, click "Open kaggle.com/settings/api", create the key with "Create Legacy API Key" and come back here.
english.KaggleOpen=Open kaggle.com/settings/api
english.KaggleFile=kaggle.json file (optional):
english.KaggleBrowse=Browse...
english.KaggleFilter=Kaggle credentials (kaggle.json)|kaggle.json|All files (*.*)|*.*
english.KaggleInvalid=That file does not look like a valid kaggle.json (it must contain "username" and "key"). Choose the file you downloaded from Kaggle with "Create Legacy API Key" or, if it is optional, leave the field empty.
english.KaggleExists=You already have Kaggle credentials saved in %1.%n%nDo you want to replace them with the selected file?
english.KaggleEmptyWarn=You did not select the Kaggle file.%n%nThe perfume database will NOT be updated (you will keep the bundled one). You can add it later by copying kaggle.json to the folder  %1.%n%nContinue without it?
; --- página de Gemini
spanish.GeminiTitle=Góngora, tu perfumista con IA (opcional)
spanish.GeminiDesc=Góngora usa la IA gratuita de Google Gemini.
spanish.GeminiBody=Para activarla necesitas una clave de API (es gratis):%n%n  1. Entra en aistudio.google.com/apikey con tu cuenta de Google.%n  2. Pulsa «Create API key» (crear clave de API) y cópiala.%n  3. Pégala aquí abajo.%n%nLa clave se guarda solo en tu ordenador. Es OPCIONAL: sin ella, Góngora responderá solo con reglas básicas (sin IA) y no podrá aconsejarte como un perfumista. Más tarde puedes añadirla con el engranaje del chat de Góngora.%n%nLa capa gratuita de Google tiene un límite diario de preguntas y puede usar las consultas para mejorar sus productos.
spanish.GeminiOpen=Abrir aistudio.google.com/apikey
spanish.GeminiKey=Clave de API de Gemini (opcional):
spanish.GeminiInvalid=Esa clave no parece válida (suele tener unos 40 caracteres y no lleva espacios). Cópiala de nuevo desde Google AI Studio o deja el campo vacío.
spanish.GeminiEmptyWarn=No has indicado la clave de Góngora.%n%nGóngora no tendrá IA (solo reglas básicas). Puedes añadirla más tarde con el engranaje del chat.%n%n¿Continuar sin ella?
english.GeminiTitle=Góngora, your AI perfumer (optional)
english.GeminiDesc=Góngora uses Google's free Gemini AI.
english.GeminiBody=To turn it on you need an API key (it is free):%n%n  1. Go to aistudio.google.com/apikey with your Google account.%n  2. Click "Create API key" and copy it.%n  3. Paste it below.%n%nThe key is stored only on your computer. It is OPTIONAL: without it, Góngora will only answer with basic rules (no AI) and cannot advise you like a perfumer. You can add it later with the gear icon in Góngora's chat.%n%nGoogle's free tier has a daily question limit and may use the queries to improve its products.
english.GeminiOpen=Open aistudio.google.com/apikey
english.GeminiKey=Gemini API key (optional):
english.GeminiInvalid=That key does not look valid (it usually has about 40 characters and no spaces). Copy it again from Google AI Studio or leave the field empty.
english.GeminiEmptyWarn=You did not enter Góngora's key.%n%nGóngora will have no AI (only basic rules). You can add it later with the gear icon in the chat.%n%nContinue without it?
; --- desinstalación
spanish.RemoveData=¿Quieres borrar también tus datos (colección, favoritas, imágenes descargadas y la clave de Góngora)?%n%nSi dices que no, se conservarán por si vuelves a instalar la app.
english.RemoveData=Do you also want to delete your data (collection, favorites, downloaded images and Góngora's key)?%n%nIf you say no, it will be kept in case you reinstall the app.

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifdef SeedDb
; base de datos inicial limpia: solo la primera vez (nunca pisa tu colección) y no se borra al desinstalar
Source: "{#SeedDb}"; DestDir: "{code:DataDir}"; DestName: "perfumappte.db"; Flags: onlyifdoesntexist uninsneveruninstall
#endif

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; actualización desde la propia app: vuelve a abrirla cuando termina
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: ShouldRelaunch

[Code]
#ifdef SeedDb
const HasSeed = True;
#else
const HasSeed = False;
#endif

var
  KagglePage, GeminiPage: TWizardPage;
  KaggleEdit, GeminiEdit: TNewEdit;
  CopyKaggle: Boolean;

function ShouldRelaunch: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:RELAUNCH|0}') = '1');
end;

function DataDir(Param: String): String;
begin
  Result := ExpandConstant('{param:DATADIR|}');
  if Result = '' then Result := ExpandConstant('{localappdata}\Perfumappte');
end;

function KaggleDir: String;
begin
  Result := ExpandConstant('{param:KAGGLEDIR|}');
  if Result = '' then Result := ExpandConstant('{%USERPROFILE}\.kaggle');
end;

function KaggleDestName(Src: String): String;
begin
  if CompareText(ExtractFileName(Src), 'access_token') = 0 then Result := 'access_token' else Result := 'kaggle.json';
end;

procedure OpenUrl(Url: String);
var ErrorCode: Integer;
begin
  ShellExec('open', Url, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

procedure KaggleOpenClick(Sender: TObject);
begin
  OpenUrl('https://www.kaggle.com/settings/api');
end;

procedure GeminiOpenClick(Sender: TObject);
begin
  OpenUrl('https://aistudio.google.com/apikey');
end;

procedure KaggleBrowseClick(Sender: TObject);
var FileName: String;
begin
  FileName := KaggleEdit.Text;
  if GetOpenFileName(CustomMessage('KaggleBrowse'), FileName, ExpandConstant('{%USERPROFILE}\Downloads'), CustomMessage('KaggleFilter'), 'json') then
    KaggleEdit.Text := FileName;
end;

{ Crea una página con un texto largo, un botón que abre una web y un campo de texto }
function MakePage(After: Integer; Title, Desc, Body, OpenCaption, EditCaption: String; var Edit: TNewEdit; OpenProc: TNotifyEvent; WithBrowse: Boolean): TWizardPage;
var
  Text, Prompt: TNewStaticText;
  OpenBtn, BrowseBtn: TNewButton;
begin
  Result := CreateCustomPage(After, Title, Desc);
  Text := TNewStaticText.Create(Result);
  Text.Parent := Result.Surface; Text.Left := 0; Text.Top := 0; Text.Width := Result.SurfaceWidth;
  Text.AutoSize := False; Text.WordWrap := True; Text.Caption := Body;
  Text.Height := Result.SurfaceHeight - ScaleY(76);
  OpenBtn := TNewButton.Create(Result);
  OpenBtn.Parent := Result.Surface; OpenBtn.Left := 0; OpenBtn.Width := ScaleX(210); OpenBtn.Height := ScaleY(23);
  OpenBtn.Top := Result.SurfaceHeight - ScaleY(70); OpenBtn.Caption := OpenCaption; OpenBtn.OnClick := OpenProc;
  Prompt := TNewStaticText.Create(Result);
  Prompt.Parent := Result.Surface; Prompt.Left := 0; Prompt.Top := Result.SurfaceHeight - ScaleY(42); Prompt.Caption := EditCaption;
  Edit := TNewEdit.Create(Result);
  Edit.Parent := Result.Surface; Edit.Left := 0; Edit.Top := Result.SurfaceHeight - ScaleY(24); Edit.Width := Result.SurfaceWidth;
  if WithBrowse then
  begin
    Edit.Width := Result.SurfaceWidth - ScaleX(88);
    BrowseBtn := TNewButton.Create(Result);
    BrowseBtn.Parent := Result.Surface; BrowseBtn.Left := Result.SurfaceWidth - ScaleX(82); BrowseBtn.Width := ScaleX(82); BrowseBtn.Height := ScaleY(23);
    BrowseBtn.Top := Edit.Top - ScaleY(1); BrowseBtn.Caption := CustomMessage('KaggleBrowse'); BrowseBtn.OnClick := @KaggleBrowseClick;
  end;
end;

procedure InitializeWizard;
begin
  if HasSeed then
    KagglePage := MakePage(wpSelectDir, CustomMessage('KaggleTitle'), CustomMessage('KaggleDesc'),
      FmtMessage(CustomMessage('KaggleBody'), [KaggleDir + '\kaggle.json']), CustomMessage('KaggleOpen'), CustomMessage('KaggleFile'), KaggleEdit, @KaggleOpenClick, True)
  else
    KagglePage := MakePage(wpSelectDir, CustomMessage('KaggleTitleNoDb'), CustomMessage('KaggleDescNoDb'),
      FmtMessage(CustomMessage('KaggleBodyNoDb'), [KaggleDir + '\kaggle.json']), CustomMessage('KaggleOpen'), CustomMessage('KaggleFileRequired'), KaggleEdit, @KaggleOpenClick, True);
  KaggleEdit.Text := ExpandConstant('{param:KAGGLEFILE|}');
  GeminiPage := MakePage(KagglePage.ID, CustomMessage('GeminiTitle'), CustomMessage('GeminiDesc'),
    CustomMessage('GeminiBody'), CustomMessage('GeminiOpen'), CustomMessage('GeminiKey'), GeminiEdit, @GeminiOpenClick, False);
  GeminiEdit.PasswordChar := '*';
  GeminiEdit.Text := ExpandConstant('{param:GEMINIKEY|}');
  CopyKaggle := False;
end;

function KaggleLooksValid(Path: String): Boolean;
var Content: AnsiString;
begin
  Result := False;
  if not FileExists(Path) then Exit;
  if CompareText(ExtractFileName(Path), 'access_token') = 0 then begin Result := True; Exit; end;
  if LoadStringFromFile(Path, Content) then
    Result := (Pos('"username"', Content) > 0) and (Pos('"key"', Content) > 0);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var Src, Dest, Key: String;
begin
  Result := True;
  if CurPageID = KagglePage.ID then
  begin
    Src := Trim(KaggleEdit.Text);
    if Src = '' then
    begin
      CopyKaggle := False;
      if not WizardSilent then
      begin
        if HasSeed then
          Result := MsgBox(FmtMessage(CustomMessage('KaggleEmptyWarn'), [KaggleDir]), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES
        else if not FileExists(KaggleDir + '\kaggle.json') then
        begin
          MsgBox(CustomMessage('KaggleRequired'), mbError, MB_OK); Result := False;
        end;
      end;
    end
    else if not KaggleLooksValid(Src) then
    begin
      MsgBox(CustomMessage('KaggleInvalid'), mbError, MB_OK); Result := False;
    end
    else
    begin
      Dest := KaggleDir + '\' + KaggleDestName(Src);
      CopyKaggle := True;
      if FileExists(Dest) and (CompareText(Src, Dest) <> 0) and (not WizardSilent) then
        CopyKaggle := MsgBox(FmtMessage(CustomMessage('KaggleExists'), [Dest]), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
      if CompareText(Src, Dest) = 0 then CopyKaggle := False;
    end;
  end
  else if CurPageID = GeminiPage.ID then
  begin
    Key := Trim(GeminiEdit.Text);
    if Key = '' then
    begin
      if (not WizardSilent) and (not FileExists(DataDir('') + '\gemini.key')) then
        Result := MsgBox(CustomMessage('GeminiEmptyWarn'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
    end
    else if (Length(Key) < 20) or (Pos(' ', Key) > 0) then
    begin
      MsgBox(CustomMessage('GeminiInvalid'), mbError, MB_OK); Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var Src, Key: String;
begin
  if CurStep = ssPostInstall then
  begin
    Src := Trim(KaggleEdit.Text);
    if CopyKaggle and (Src <> '') then
    begin
      ForceDirectories(KaggleDir);
      CopyFile(Src, KaggleDir + '\' + KaggleDestName(Src), False);
    end;
    Key := Trim(GeminiEdit.Text);
    if Key <> '' then
    begin
      ForceDirectories(DataDir(''));
      SaveStringToFile(DataDir('') + '\gemini.key', Key, False);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
    if MsgBox(CustomMessage('RemoveData'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      DelTree(DataDir(''), True, True, True);
end;

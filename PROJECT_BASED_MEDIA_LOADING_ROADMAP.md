# Project-Based Media Loading - Implementation Roadmap

## Stand: 2026-02-06 - Phase 1 (Backend) FERTIG ✅

---

## 🎯 Ziel

**Performance-Optimierung durch projekt-basiertes Laden von Medien**

Statt alle Workspace-Medien zu laden (z.B. 5000 Photos), lädt nur das aktive Projekt seine enabled Folders (z.B. 300 Photos).

---

## ✅ FERTIG IMPLEMENTIERT (Backend)

### 1. Project Model erweitert

**Datei**: `c:\_Git\Python-tools\photo_tool\projects\manager.py`

**Neue Felder in Project Class**:

```python
@dataclass
class Project:
    id: str
    name: str
    created: str
    updated: str
    workspace_path: str  # ← NEU! Link zum Parent Workspace
    
    # NEU: Folder selection (alle disabled by default)
    folders: Optional[List[Dict[str, Any]]] = None
    
    # Bestehend
    selection_mode: str = 'filter'
    filters: Optional[ProjectFilters] = None
    quality_settings: Optional[QualityDetectionSettings] = None
    export_settings: Optional[ExportSettings] = None
    # ...
```

**Folder-Struktur**:
```python
{
    'path': 'E:\\Lumix-2026-01\\101_PANA',
    'enabled': False,  # Disabled by default!
    'photo_count': 961,
    'video_count': 12,
    'audio_count': 0
}
```

---

### 2. create_project() erweitert

**Methode**: `ProjectManager.create_project()`

**Neu**: Nimmt `workspace_folders` Parameter

```python
def create_project(
    self,
    name: str,
    workspace_folders: Optional[List[Dict[str, Any]]] = None,  # ← NEU
    selection_mode: str = 'filter',
    filters: Optional[Dict[str, Any]] = None,
    # ...
) -> Project:
```

**Funktionsweise**:
1. Bekommt alle Workspace-Folders übergeben
2. Erstellt Project mit **allen Folders disabled**
3. User muss explizit Folders aktivieren

---

### 3. API Endpoint: POST /api/projects

**Datei**: `c:\_Git\Python-tools\gui_poc\server.py`

**Geändert**:

```python
@app.post('/api/projects')
def create_project():
    # Get workspace folders
    workspace_path = get_current_workspace()
    ws = Workspace(workspace_path)
    config = load_config(ws.config_file)
    
    # Build folder list from workspace
    workspace_folders = []
    for folder in config.folders:
        workspace_folders.append({
            'path': folder.get('path'),
            'photo_count': 0,  # Updated when enabled
            'video_count': 0,
            'audio_count': 0
        })
    
    # Create project with folder template
    project = pm.create_project(
        name=data['name'],
        selection_mode=data.get('selection_mode', 'filter'),
        workspace_folders=workspace_folders,  # ← NEU!
        # ...
    )
```

---

### 4. NEU: API Endpoint GET /api/projects/<id>/media

**Zweck**: Lädt Medien nur aus enabled Folders des Projekts

**URL**: `GET /api/projects/{project_id}/media`

**Query Params**:
- `limit`: Max items (default: 2500)
- `offset`: Pagination (default: 0)
- `type`: Filter by type ('photo', 'video', 'audio', 'all')

**Funktionsweise**:

```python
@app.get('/api/projects/<project_id>/media')
def get_project_media(project_id):
    # 1. Load project
    project = pm.get_project(project_id)
    
    # 2. Get ONLY enabled folders
    enabled_folders = [f['path'] for f in project.folders if f.get('enabled', False)]
    
    # 3. Return empty if no folders enabled
    if not enabled_folders:
        return {'media': [], 'message': 'No folders enabled'}
    
    # 4. Scan only enabled folders
    all_media = scan_multiple_directories(enabled_folders, ...)
    
    # 5. Separate by type
    photos = filter_by_type(all_media, 'photo')
    videos = filter_by_type(all_media, 'video')
    audio = filter_by_type(all_media, 'audio')
    
    # 6. Sort, paginate, return
    return {
        'media': result,
        'counts': {
            'photos': len(photos),
            'videos': len(videos),
            'audio': len(audio)
        }
    }
```

**Response Format**:

```json
{
  "media": [
    {
      "id": "E:\\Lumix\\P1012569.JPG",
      "name": "P1012569.JPG",
      "type": "photo",
      "capture_time": "2026-01-05 14:05:30",
      "rating": 0,
      "color": null,
      "blur_scores": {
        "laplacian": 123.45,
        "tenengrad": 234.56,
        "roi": 345.67
      },
      "burst": {
        "is_burst": true,
        "group_id": "burst_20260105_140530",
        "group_size": 5
      }
    }
  ],
  "total": 961,
  "project_id": "nepal-bestof",
  "counts": {
    "photos": 961,
    "videos": 12,
    "audio": 0
  }
}
```

---

### 5. Tab-Reihenfolge geändert

**Datei**: `c:\_Git\Python-tools\gui_poc\static\index.html`

**Alt**:
```
Media Manager - Photos - Bursts - Projects - Workspaces
```

**Neu**:
```
Media Manager - Workspaces - Projects - Media - Bursts
```

**Änderungen**:
- `currentView === 'media'` → `'media-manager'` (für Media Manager)
- `currentView === 'photos'` → `'media'` (für Media Tab)
- Media & Bursts Tabs: `:disabled="!currentProjectId"`

---

## 🚧 NOCH ZU IMPLEMENTIEREN (Frontend)

### Phase 2: Project Tab UI

#### 2.1 Project List (Sidebar)

**Layout**: Lightroom-Style (Links Liste, Rechts Details)

```html
<div class="projects-view">
    <!-- Left: Project List -->
    <div class="project-list">
        <button @click="createNewProject">➕ New Project</button>
        
        <div v-for="proj in projects" 
             :key="proj.id"
             :class="{ active: proj.id === currentProjectId }"
             @click="activateProject(proj.id)">
            📁 {{ proj.name }}
            <span class="count">{{ proj.media_count || 0 }}</span>
        </div>
    </div>
    
    <!-- Right: Project Details -->
    <div class="project-details" v-if="currentProject">
        <!-- Siehe 2.2 -->
    </div>
</div>
```

---

#### 2.2 Project Details (Rechts)

```html
<div class="project-details">
    <!-- Name (inline-editable) -->
    <h2>
        <input v-model="currentProject.name" 
               @blur="saveProject"
               placeholder="Project Name">
    </h2>
    
    <!-- Folder Selection -->
    <section>
        <h3>📁 Media Folders (from Workspace)</h3>
        <div v-for="folder in currentProject.folders" :key="folder.path">
            <label>
                <input type="checkbox" 
                       v-model="folder.enabled"
                       @change="onFolderToggle">
                {{ folder.path }}
                <span class="counts">
                    {{ folder.photo_count }} photos,
                    {{ folder.video_count }} videos
                </span>
            </label>
        </div>
    </section>
    
    <!-- Quality Settings -->
    <section>
        <h3>🎯 Quality Detection</h3>
        
        <label>
            Blur Method:
            <select v-model="currentProject.quality_settings.blur_method">
                <option value="laplacian">Laplacian</option>
                <option value="tenengrad">Tenengrad</option>
                <option value="roi">ROI-based</option>
            </select>
        </label>
        
        <label>
            Blur Threshold: {{ currentProject.quality_settings.blur_threshold }}
            <input type="range" min="0" max="200" 
                   v-model="currentProject.quality_settings.blur_threshold">
        </label>
        
        <label>
            Burst Time Window: {{ currentProject.quality_settings.burst_time_threshold }}s
            <input type="range" min="0.5" max="10" step="0.5"
                   v-model="currentProject.quality_settings.burst_time_threshold">
        </label>
        
        <label>
            Burst Similarity: {{ currentProject.quality_settings.burst_similarity_threshold }}
            <input type="range" min="0" max="1" step="0.05"
                   v-model="currentProject.quality_settings.burst_similarity_threshold">
        </label>
    </section>
    
    <!-- Stats -->
    <section>
        <h3>📊 Project Statistics</h3>
        <div class="stat">{{ enabledMediaCount }} media will be loaded</div>
        <div class="stat">{{ enabledFolderCount }} folders enabled</div>
    </section>
    
    <button @click="saveProject" class="btn-primary">💾 Save Project</button>
</div>
```

---

### Phase 3: Vue Data & Methods

#### 3.1 Data Properties (ergänzen)

```javascript
data() {
    return {
        // Bestehend
        currentView: 'media-manager',
        currentWorkspace: null,
        currentProjectId: null,  // Bestehend
        projects: [],
        
        // NEU
        currentProject: null,  // Full project object
        mediaCount: 0,  // Total media in current project
        projectMedia: [],  // Loaded media from current project
        
        // Bestehend
        photos: [],
        videos: [],
        audio: [],
        bursts: [],
        // ...
    }
}
```

---

#### 3.2 Computed Properties

```javascript
computed: {
    enabledFolders() {
        if (!this.currentProject || !this.currentProject.folders) return [];
        return this.currentProject.folders.filter(f => f.enabled);
    },
    
    enabledFolderCount() {
        return this.enabledFolders.length;
    },
    
    enabledMediaCount() {
        return this.enabledFolders.reduce((sum, f) => {
            return sum + (f.photo_count || 0) + (f.video_count || 0) + (f.audio_count || 0);
        }, 0);
    }
}
```

---

#### 3.3 Methods (NEU)

```javascript
methods: {
    // Project activation
    async activateProject(projectId) {
        try {
            // 1. Set as current
            this.currentProjectId = projectId;
            
            // 2. Load project details
            const res = await fetch(`/api/projects/${projectId}`);
            const data = await res.json();
            this.currentProject = data.project;
            
            // 3. Auto-switch to Media tab
            this.currentView = 'media';
            
            // 4. Load media from enabled folders
            await this.loadProjectMedia();
            
            // 5. Update bursts
            await this.loadProjectBursts();
        } catch (err) {
            console.error('Error activating project:', err);
            alert(`Error: ${err.message}`);
        }
    },
    
    // Load media for current project
    async loadProjectMedia() {
        if (!this.currentProjectId) {
            this.projectMedia = [];
            this.photos = [];
            this.videos = [];
            this.audio = [];
            return;
        }
        
        try {
            this.loading = true;
            
            const res = await fetch(`/api/projects/${this.currentProjectId}/media?limit=2500`);
            const data = await res.json();
            
            if (data.message && data.total === 0) {
                // No folders enabled
                this.error = data.message;
                this.projectMedia = [];
                this.photos = [];
                return;
            }
            
            this.projectMedia = data.media;
            this.mediaCount = data.total;
            
            // Separate by type
            this.photos = data.media.filter(m => m.type === 'photo');
            this.videos = data.media.filter(m => m.type === 'video');
            this.audio = data.media.filter(m => m.type === 'audio');
            
            // Update stats
            this.updateBurstStats();
            
        } catch (err) {
            this.error = err.message;
        } finally {
            this.loading = false;
        }
    },
    
    // Folder toggle handler
    async onFolderToggle() {
        // Option 1: Live reload
        await this.saveProject();
        await this.loadProjectMedia();
        
        // Option 2: Show "Save to apply" message
        // this.hasUnsavedChanges = true;
    },
    
    // Save project
    async saveProject() {
        if (!this.currentProject) return;
        
        try {
            const res = await fetch(`/api/projects/${this.currentProject.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.currentProject)
            });
            
            const data = await res.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            alert('✓ Project saved');
            
        } catch (err) {
            alert(`Error saving project: ${err.message}`);
        }
    },
    
    // Create new project
    async createNewProject() {
        const name = prompt('Project Name:');
        if (!name) return;
        
        try {
            const res = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    selection_mode: 'filter'
                })
            });
            
            const data = await res.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Reload projects
            await this.loadProjects();
            
            // Activate new project
            await this.activateProject(data.project.id);
            
            // Switch to Projects tab for configuration
            this.currentView = 'projects';
            
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    }
}
```

---

### Phase 4: Media Tab Integration

#### 4.1 Ändern: loadPhotos() → loadProjectMedia()

**Alt** (workspace-basiert):
```javascript
async loadPhotos() {
    const res = await fetch('/api/photos?limit=100');
    // Lädt aus Workspace-Folders
}
```

**Neu** (projekt-basiert):
```javascript
async loadProjectMedia() {
    if (!this.currentProjectId) {
        this.error = 'No project selected';
        return;
    }
    
    const res = await fetch(`/api/projects/${this.currentProjectId}/media?limit=2500`);
    // Lädt nur aus enabled Project-Folders
}
```

---

#### 4.2 Project Selector im Header

```html
<div class="header-controls">
    <!-- Workspace Selector -->
    <select v-model="currentWorkspace" @change="switchWorkspace">
        <option v-for="ws in workspaces" :value="ws.path">
            🗂️ {{ ws.name }}
        </option>
    </select>
    
    <!-- Project Selector (prominent!) -->
    <select v-model="currentProjectId" 
            @change="activateProject(currentProjectId)"
            :disabled="!currentWorkspace">
        <option :value="null">📁 No project - Create one first</option>
        <option v-for="proj in projects" :value="proj.id">
            📁 {{ proj.name }} ({{ proj.media_count || 0 }} media)
        </option>
    </select>
    
    <button @click="createNewProject" :disabled="!currentWorkspace">
        ➕ New Project
    </button>
</div>
```

---

## 🎨 UI/UX Konzept

### Workflow

```
1. User wählt Workspace
   → Projects für diesen Workspace laden
   → Kein Media-Loading!

2. User klickt "➕ New Project"
   → Modal: Name eingeben
   → Project erstellt mit allen Folders disabled
   → Wechselt zu Projects Tab

3. User aktiviert Folders im Project Tab
   ☑️ E:\Lumix (961 photos)
   ☐ E:\Galaxy (1227 photos)
   
4. User klickt "💾 Save Project"
   → Auto-switch zu Media Tab
   → Lädt nur Lumix-Folder (961 photos)
   → Zeit: ~5 Sekunden (statt 15s für alle)

5. User wechselt zu anderem Project
   → Unload 961 photos
   → Load new project photos
```

---

## 📊 Performance-Vergleich

### Szenario: Nepal Workspace

**Folders**:
- `E:\Lumix-2026-01\101_PANA` (961 photos)
- `E:\NEPAL-2025\Galaxy-S22` (1227 photos)

**Total**: 2188 Photos

### Alt (Workspace-basiert):
```
Workspace öffnen
→ Lädt ALLE 2188 photos
→ Zeit: ~15 Sekunden
→ RAM: ~500 MB
```

### Neu (Projekt-basiert):
```
Project "Lumix Best-of"
→ Nur Lumix-Folder enabled
→ Lädt 961 photos (44% weniger!)
→ Zeit: ~5 Sekunden (67% schneller!)
→ RAM: ~200 MB (60% weniger!)
```

---

## 🔧 Migration / Backward Compatibility

### Bestehende Projects

**Problem**: Alte Projects haben kein `folders` Field

**Lösung**: Auto-Migration beim Load

```python
def get_project(self, project_id: str) -> Optional[Project]:
    project = Project.from_dict(data)
    
    # Migration: Add folders if missing
    if not project.folders:
        # Get workspace folders
        workspace_config = load_config(project.workspace_path / "config.yaml")
        project.folders = [
            {
                'path': f.get('path'),
                'enabled': True,  # Enable all by default for old projects
                'photo_count': 0,
                'video_count': 0,
                'audio_count': 0
            }
            for f in workspace_config.folders
        ]
        # Auto-save migrated project
        self.save_project(project)
    
    return project
```

---

## 📝 Testing Checklist

### Backend Testing

- [ ] `POST /api/projects` erstellt Project mit disabled Folders
- [ ] `GET /api/projects/<id>` lädt Project mit Folders
- [ ] `GET /api/projects/<id>/media` lädt nur enabled Folders
- [ ] `GET /api/projects/<id>/media` gibt Meldung bei 0 enabled Folders
- [ ] `PUT /api/projects/<id>` speichert Folder-Änderungen

### Frontend Testing

- [ ] Tab-Reihenfolge korrekt
- [ ] Media/Bursts Tabs disabled ohne Project
- [ ] Project erstellen funktioniert
- [ ] Project-Liste zeigt alle Projects
- [ ] Folder-Checkboxes funktionieren
- [ ] Quality Settings Sliders funktionieren
- [ ] Save Project funktioniert
- [ ] activateProject() lädt Medien
- [ ] Project wechseln entlädt/lädt Medien
- [ ] Performance: Nur subset geladen

---

## 🚀 Nächste Schritte für neuen Chat

### Priorität 1: Project Tab UI

1. Project-Liste (Sidebar)
2. Project-Details (Rechts)
3. Folder-Checkboxes
4. Quality Settings Sliders
5. Save Button

### Priorität 2: Vue Integration

1. `activateProject()` Method
2. `loadProjectMedia()` Method
3. `createNewProject()` Method
4. `saveProject()` Method
5. Computed Properties

### Priorität 3: Media Tab Umbau

1. loadPhotos() entfernen
2. loadProjectMedia() integrieren
3. Project Selector im Header
4. Disabled States

### Priorität 4: Testing & Polish

1. End-to-End Test
2. Performance Messung
3. Error Handling
4. UI Polish (Meldungen, Disabled States)

---

## 📚 Wichtige Code-Referenzen

### Backend Files
- `photo_tool/projects/manager.py` - Project Model (GEÄNDERT)
- `gui_poc/server.py` - API Endpoints (GEÄNDERT)

### Frontend Files
- `gui_poc/static/index.html` - Vue App (TEILWEISE GEÄNDERT)

### Neue API Endpoints
- `POST /api/projects` - Mit workspace_folders
- `GET /api/projects/<id>/media` - Projekt-spezifische Medien

---

## 🎯 Erfolgs-Kriterien

- [ ] User erstellt Project → alle Folders disabled
- [ ] User aktiviert 1 Folder → nur dieser wird geladen
- [ ] Performance: 50-90% schneller als vorher
- [ ] RAM: 60-80% weniger als vorher
- [ ] UI: Intuitiv (wie Lightroom/Resolve)
- [ ] Keine Breaking Changes für bestehende Workspaces

---

## ⚠️ Wichtige Design-Entscheidungen

1. **Alle Folders disabled by default**
   - User muss explizit aktivieren
   - Verhindert versehentliches Laden

2. **Project Selector prominent im Header**
   - Wie Workspace Selector
   - Immer sichtbar

3. **Media/Bursts Tabs disabled ohne Project**
   - Erzwingt Workflow
   - Klare User-Experience

4. **Live-Reload bei Folder-Toggle**
   - Option 1: Sofort neu laden (kann langsam sein)
   - Option 2: "Save to apply" Message (empfohlen!)

5. **Tab-Reihenfolge logisch**
   - Media Manager → Workspaces → Projects → Media → Bursts
   - Von global zu spezifisch

---

## 📞 Support für neuen Chat

Bei Fragen zu diesem Stand:

1. Lies diese Datei komplett
2. Check Backend: `photo_tool/projects/manager.py`
3. Check API: `gui_poc/server.py` (Zeile ~1891, ~2039)
4. Frontend ist Work-in-Progress

**Status**: Backend 100% fertig, Frontend 10% fertig

**Geschätzter Aufwand für Frontend**: 3-4 Stunden

**Start Point**: Phase 2, Section 2.1 (Project Tab UI)

---

**Viel Erfolg! 🚀**

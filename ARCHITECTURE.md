# Photo Tool Architecture

This document describes the architecture of Photo Tool, designed for future extensibility to a client/server web application.

## Overview

Photo Tool follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         Interface Layer                  │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐│
│  │   CLI   │  │ Desktop  │  │  Web    ││
│  │ (Typer) │  │   GUI    │  │ Browser ││
│  └─────────┘  └──────────┘  └─────────┘│
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│          API Layer (Future)             │
│  ┌─────────────────────────────────┐   │
│  │      GraphQL / REST API         │   │
│  │      (FastAPI + Strawberry)     │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Core Business Logic             │
│  ┌──────────┐  ┌──────────┐            │
│  │ Analysis │  │ Actions  │            │
│  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐            │
│  │   I/O    │  │  Config  │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Data Layer                      │
│  ┌──────────┐  ┌──────────┐            │
│  │ Database │  │  Cache   │            │
│  │ (SQLite) │  │  (Files) │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
```

## Current Implementation (v0.1 - CLI)

### Module Structure

```
photo_tool/
├── cli/              # CLI interface (Typer)
│   ├── main.py
│   └── commands_*.py
├── config/           # Configuration management
│   ├── schema.py     # Pydantic models
│   └── load.py       # YAML loading
├── workspace/        # Workspace & project management
│   ├── model.py      # Workspace structure
│   ├── init.py       # Creation logic
│   └── db.py         # SQLite wrapper
├── io/               # File I/O operations
│   ├── scanner.py    # Find files
│   ├── exif.py       # EXIF reading
│   └── thumbnails.py # Thumbnail cache
├── analysis/         # Photo analysis
│   ├── time_grouping.py    # Stage 1: Time-based
│   ├── clustering.py       # Stage 3: Cluster similar
│   └── similarity/         # Stage 2: Visual similarity
│       ├── phash.py        # Perceptual hashing
│       ├── blur.py         # Quality detection
│       ├── ssim.py         # SSIM refinement
│       └── exposure.py     # Histogram analysis
├── actions/          # Operations on photos
│   ├── organizer.py  # Move/organize files
│   ├── rating.py     # Rating system
│   └── dedupe.py     # Deduplication
├── report/           # Report generation
│   ├── text_report.py
│   └── html_report.py
├── editing/          # (Future) Image editing
├── ui/               # (Future) GUI widgets
└── util/             # Utilities
    ├── logging.py
    ├── paths.py
    └── timing.py
```

## Three-Stage Pipeline

The core analysis follows a multi-stage pipeline for efficiency:

### Stage 1: Time-Based Grouping
**Purpose:** Fast pre-filtering to create candidate groups

```python
# Input: All photos + EXIF timestamps
# Output: Groups of photos taken within time window
time_groups = group_by_time(photos, timestamps, window=3.0)
```

**Algorithm:**
1. Sort photos by capture time (EXIF DateTimeOriginal or file mtime)
2. Group consecutive photos if:
   - Gap between photos ≤ `max_gap` (default 2s)
   - Total duration ≤ `time_window` (default 3s)
3. Only keep groups with ≥ 2 photos

**Performance:** O(n log n) - very fast, even for 100k+ photos

### Stage 2: Visual Similarity
**Purpose:** Compute perceptual hashes for fast comparison

```python
# Input: Time-based candidate groups
# Output: Perceptual hash for each photo
for photo in group.photos:
    hash = compute_phash(photo, method="phash")
```

**Methods:**
- **pHash** (default): Most robust, best for general use
- **dHash**: Faster, good for nearly identical photos
- **aHash**: Simplest, least accurate

**Comparison:** Hamming distance between hashes
- Distance 0-5: Very similar
- Distance 6-10: Similar
- Distance 10+: Different

**Optional Refinement:** SSIM (Structural Similarity)
- Slower but more accurate
- Good for confirming close matches

### Stage 3: Clustering
**Purpose:** Group similar photos within time windows

```python
# Input: Hashes + similarity threshold
# Output: Clusters of similar photos
clusters = cluster_similar_photos(time_groups, threshold=6)
```

**Algorithm:**
1. For each photo in time group:
   - Compare hash to all subsequent photos
   - If distance ≤ threshold, add to cluster
2. Track "best" photo (highest blur/sharpness score)

**Performance:** O(n²) within groups, but groups are small (typically 2-10 photos)

## Data Models

### Core Data Classes

```python
@dataclass
class PhotoFile:
    """Basic file information"""
    path: Path
    filename: str
    size_bytes: int
    modified_time: datetime
    extension: str

@dataclass
class TimeGroup:
    """Photos grouped by time"""
    photos: List[Path]
    capture_times: List[datetime]
    start_time: datetime
    end_time: datetime

@dataclass
class PhotoCluster:
    """Visually similar photos"""
    photos: List[Path]
    hashes: List[str]
    blur_scores: List[float]
    
    @property
    def best_photo(self) -> Path:
        """Returns sharpest photo"""
```

### Configuration (Pydantic)

```python
class PhotoToolConfig(BaseModel):
    workspace: WorkspaceConfig
    scan: ScanConfig
    grouping: GroupingConfig
    similarity: SimilarityConfig
    quality: QualityConfig
    actions: ActionsConfig
```

All settings validated with Pydantic, loaded from YAML.

## Future: Client/Server Architecture

### Planned Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (Browser)              │
│  ┌────────────────────────────────┐    │
│  │  React / Vue.js                │    │
│  │  - Filmstrip viewer            │    │
│  │  - Histogram display           │    │
│  │  - Rating interface            │    │
│  │  - Apollo Client (GraphQL)     │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
              │ HTTP / WebSocket
              ▼
┌─────────────────────────────────────────┐
│         Backend (Python)                │
│  ┌────────────────────────────────┐    │
│  │  FastAPI                       │    │
│  │  ┌──────────────────────────┐  │    │
│  │  │  GraphQL (Strawberry)    │  │    │
│  │  │  - Query: photos, albums │  │    │
│  │  │  - Mutation: organize    │  │    │
│  │  │  - Subscription: progress│  │    │
│  │  └──────────────────────────┘  │    │
│  │                                 │    │
│  │  ┌──────────────────────────┐  │    │
│  │  │  Core Logic (reused!)    │  │    │
│  │  │  - Analysis pipeline     │  │    │
│  │  │  - Actions               │  │    │
│  │  └──────────────────────────┘  │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Database (PostgreSQL)           │
│  - Photo index                          │
│  - User preferences                     │
│  - Ratings & tags                       │
└─────────────────────────────────────────┘
```

### GraphQL Schema (Planned)

```graphql
type Photo {
  id: ID!
  path: String!
  filename: String!
  capturedAt: DateTime
  width: Int!
  height: Int!
  
  # Quality metrics
  blurScore: Float
  exposureScore: Float
  
  # Perceptual hash
  phash: String!
  
  # Relations
  cluster: PhotoCluster
  rating: Int
  tags: [String!]
}

type PhotoCluster {
  id: ID!
  photos: [Photo!]!
  bestPhoto: Photo!
  createdAt: DateTime!
}

type Query {
  # Search
  photos(
    after: DateTime
    before: DateTime
    minBlurScore: Float
    tags: [String!]
    limit: Int
  ): [Photo!]!
  
  # Clusters
  clusters(minSize: Int): [PhotoCluster!]!
  
  # Workspace
  workspace: Workspace!
}

type Mutation {
  # Organization
  organizeBursts(
    dryRun: Boolean!
    minGroupSize: Int
  ): OrganizeResult!
  
  # Rating
  setRating(photoId: ID!, rating: Int!): Photo!
  
  # Deduplication
  deduplicate(
    strategy: DedupeStrategy!
    action: DedupeAction!
  ): DedupeResult!
}

type Subscription {
  # Real-time progress
  scanProgress: ScanProgress!
  analysisProgress: AnalysisProgress!
}
```

### API Implementation Plan

1. **Phase 1: REST Endpoints** (simple, quick)
   - GET /photos
   - POST /analyze
   - POST /organize
   - GET /workspace/info

2. **Phase 2: GraphQL** (flexible queries)
   - Implement Strawberry GraphQL schema
   - Resolvers call existing core logic
   - WebSocket for real-time updates

3. **Phase 3: Frontend**
   - React/Vue app
   - Apollo Client for GraphQL
   - Components:
     - Filmstrip viewer (virtualized list)
     - Lightbox with EXIF panel
     - Histogram overlay
     - Batch operations UI

### Database Migration

**Current:** SQLite (simple, local)

**Future:** PostgreSQL (for web app)
- Multi-user support
- Better concurrency
- Full-text search
- JSONB for flexible metadata

**Migration Strategy:**
- Keep SQLite for local/CLI use
- Add PostgreSQL adapter in `workspace/db.py`
- Same interface, different backend
- Use SQLAlchemy ORM for abstraction

## Design Principles

### 1. Separation of Concerns
- **Core logic** is independent of interface (CLI/GUI/API)
- Each module has single responsibility
- Clear boundaries between layers

### 2. Testability
- Business logic in pure functions where possible
- Dependency injection for I/O
- Mock-friendly interfaces

### 3. Performance
- Cache expensive operations (hashes, thumbnails)
- Process in stages (time → hash → cluster)
- Progress bars for long operations

### 4. Safety
- Dry-run mode by default
- No destructive operations without confirmation
- Preserve EXIF metadata
- Undo-friendly (moves, not deletes)

### 5. Extensibility
- Plugin architecture for similarity methods
- Configurable pipelines
- Easy to add new analysis types

## Technology Stack

### Current (v0.1)
- **CLI:** Typer + Rich
- **Config:** PyYAML + Pydantic
- **Image:** Pillow + OpenCV
- **Hashing:** imagehash
- **Quality:** scikit-image
- **DB:** SQLite (basic)

### Future (v1.0+)
- **API:** FastAPI + Strawberry GraphQL
- **Frontend:** React/Vue + Apollo Client
- **DB:** PostgreSQL + SQLAlchemy
- **Cache:** Redis (optional)
- **Queue:** Celery (for background jobs)
- **Deploy:** Docker + docker-compose

## Performance Considerations

### Scaling Strategy

| Photos | Strategy | Expected Time |
|--------|----------|---------------|
| 100-1k | In-memory | Seconds |
| 1k-10k | SQLite + cache | Minutes |
| 10k-100k | PostgreSQL + Redis | 10-30 min |
| 100k+ | Batch processing + workers | Hours |

### Optimization Techniques

1. **Thumbnail Cache:** Generate once, reuse forever
2. **Hash Cache:** Store in DB, recompute only on file change
3. **Batch Processing:** Process in chunks of 1000 photos
4. **Parallel Processing:** multiprocessing for hash computation
5. **Incremental Scan:** Only process new/changed files

## Testing Strategy

### Unit Tests
- Pure functions (hashing, grouping, clustering)
- No file I/O in unit tests
- Mock external dependencies

### Integration Tests
- Test with real (small) image sets
- Verify EXIF reading, thumbnail generation
- Database operations

### End-to-End Tests
- CLI command workflows
- Full pipeline (scan → analyze → organize)
- Dry-run validation

## Security Considerations (for Web Version)

1. **File Access Control**
   - User isolation (each user sees only their photos)
   - Path traversal prevention
   - Sanitize filenames

2. **API Security**
   - Authentication (JWT tokens)
   - Rate limiting
   - Input validation (Pydantic)

3. **Data Privacy**
   - EXIF data can contain location
   - Optional EXIF stripping on export
   - Secure thumbnail storage

## Roadmap

### v0.1 (Current) - CLI MVP
- [x] Workspace management
- [x] Photo scanning + EXIF
- [x] Time-based grouping
- [x] Perceptual hashing
- [x] Burst detection
- [x] Quality analysis (blur)
- [x] Organization (folders)
- [x] Reports (text, HTML)

### v0.2 - Enhanced CLI
- [ ] RAW format support (RW2, CR3)
- [ ] Advanced filtering
- [ ] Batch rating
- [ ] Export presets
- [ ] Performance optimization

### v0.3 - Desktop GUI
- [ ] PySide6 app
- [ ] Filmstrip viewer
- [ ] Lightbox
- [ ] Histogram display
- [ ] Visual clustering

### v1.0 - Web Application
- [ ] FastAPI backend
- [ ] GraphQL API
- [ ] React frontend
- [ ] Real-time updates
- [ ] Multi-user support
- [ ] Cloud deployment

---

**Note:** This architecture is designed to minimize rework when transitioning from CLI to web app. Core business logic remains unchanged, only interfaces are added.

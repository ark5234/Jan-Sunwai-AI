$file = 'c:\Users\Vikra\OneDrive\Desktop\Jan-Sunwai AI\docs\PROJECT_REPORT.md'
$text = [System.IO.File]::ReadAllText($file)

$old = @ "
#### 5.2.9 Deployment Diagram

`mermaid
graph TB
    subgraph Client ["Client Machine"]
        Browser["Web Browser\nChrome / Firefox / Edge"]
    end

    subgraph Host ["Host Machine (Windows 11 / Ubuntu 22.04)"]
        subgraph DockerNet ["Docker Network"]
            MongoDB[("MongoDB\n:27017")]
        end

        subgraph PythonEnv ["Python Virtual Environment (.venv)"]
            Backend["FastAPI + Uvicorn\n:8000"]
        end

        subgraph NodeEnv ["Node.js"]
            Frontend["Vite Dev Server\n:5173"]
        end

        Ollama["Ollama Daemon\n:11434"]
        GPU["NVIDIA GPU\n≥4 GB VRAM"]
    end

    subgraph CDN ["External CDNs (internet)"]
        CARTO["CARTO Tile CDN\n(street tiles)"]
        ESRI["ESRI ArcGIS CDN\n(satellite tiles)"]
    end

    Browser -->|"HTTP :5173"| Frontend
    Browser -->|"REST API :8000"| Backend
    Browser -->|"HTTPS (map tiles)"| CARTO
    Browser -->|"HTTPS (satellite)"| ESRI
    Backend -->|"Motor TCP :27017"| MongoDB
    Backend -->|"HTTP :11434"| Ollama
    Ollama --> GPU
`
"

$text = $text.Replace($old, $old.Replace('≥4', '>= 4'))
[System.IO.File]::WriteAllText($file, $text, [System.Text.Encoding]::UTF8)
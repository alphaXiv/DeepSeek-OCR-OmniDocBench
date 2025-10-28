import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import rehypeRaw from 'rehype-raw'
import 'katex/dist/katex.min.css'
import './App.css'

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [ocrResult, setOcrResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const [copied, setCopied] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    // Check URL parameter for theme - handle both search and hash
    const searchParams = new URLSearchParams(window.location.search)
    const hashParams = new URLSearchParams(window.location.hash.split('?')[1])
    const themeParam = searchParams.get('theme') || hashParams.get('theme')
    
    if (themeParam === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.setAttribute('data-theme', 'light')
    }
  }, [])

  const isValidFile = (file) => {
    const validTypes = [
      'application/pdf',
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/bmp'
    ]
    return file && validTypes.includes(file.type)
  }

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0]
    if (isValidFile(file)) {
      setSelectedFile(file)
      setError('')
      setOcrResult('')
    } else {
      setError('Please select a valid PDF or image file (JPEG, PNG, GIF, WebP, BMP)')
      setSelectedFile(null)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const file = e.dataTransfer.files?.[0]
    if (isValidFile(file)) {
      setSelectedFile(file)
      setError('')
      setOcrResult('')
    } else {
      setError('Please drop a valid PDF or image file')
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first')
      return
    }

    setLoading(true)
    setError('')
    setOcrResult('')

    const formData = new FormData()
    formData.append('file', selectedFile)

    // Auto-detect file type and route to appropriate endpoint
    const isPdf = selectedFile.type === 'application/pdf'
    const endpoint = isPdf ? 'pdf' : 'image'

    // Cache busting
    const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    const url = `https://alphaxiv--deepseek-ocr-modal-serve.modal.run/run/${endpoint}?_r=${requestId}`

    console.info(`Uploading ${isPdf ? 'PDF' : 'Image'}:`, { requestId, fileName: selectedFile.name, endpoint })

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Cache-Control': 'no-cache, no-store',
          'Pragma': 'no-cache',
          'X-Request-Id': requestId,
        },
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const data = await response.json()
      let ocrText = data.ocr_text || 'No text extracted'
      
      // Convert LaTeX delimiters to formats KaTeX understands
      // Convert \( ... \) to $ ... $
      ocrText = ocrText.replace(/\\\(/g, '$').replace(/\\\)/g, '$')
      // Convert \[ ... \] to $$ ... $$
      ocrText = ocrText.replace(/\\\[/g, '$$').replace(/\\\]/g, '$$')
      
      // Convert HTML tags to markdown equivalents to preserve math rendering
      // Replace <center> tags with a div wrapper we can style
      ocrText = ocrText.replace(/<center>/gi, '\n\n<div class="figure-caption">\n\n')
      ocrText = ocrText.replace(/<\/center>/gi, '\n\n</div>\n\n')
      
      setOcrResult(ocrText)
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setSelectedFile(null)
    setOcrResult('')
    setError('')
    setCopied(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(ocrResult)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <>
      <div className="container">
        <h1>DeepSeek OCR</h1>
        <p className="subtitle">Upload a PDF or image to extract text using AI-powered OCR</p>

        <div 
          className={`upload-area ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/gif,image/webp,image/bmp"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <div className="upload-content">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="upload-text">
              {selectedFile ? selectedFile.name : 'Drop file here or click to browse'}
            </p>
            <p className="upload-hint">PDF or image files (JPEG, PNG, GIF, WebP, BMP)</p>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="button-group">
          <button 
            onClick={handleUpload} 
            disabled={!selectedFile || loading}
            className="btn btn-primary"
          >
            {loading ? 'Processing...' : 'Extract Text'}
          </button>
          {selectedFile && (
            <button 
              onClick={handleReset}
              disabled={loading}
              className="btn btn-secondary"
            >
              Clear
            </button>
          )}
        </div>

        {ocrResult && (
          <div className="result-container">
            <div className="result-header">
              <h2>Extracted Text:</h2>
              <button 
                onClick={handleCopy}
                className="btn btn-copy"
                title="Copy to clipboard"
              >
                {copied ? (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                    Copy
                  </>
                )}
              </button>
            </div>
            <div className="result-text">
              <ReactMarkdown
                remarkPlugins={[remarkMath, remarkGfm]}
                rehypePlugins={[rehypeRaw, rehypeKatex]}
              >
                {ocrResult}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

export default App

const { useState, useEffect, useRef } = React;

// MAPS AI Scripting Assistant Logo Component
const MapsAILogo = ({ size = 120, showText = true }) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 256 256" 
      xmlns="http://www.w3.org/2000/svg" 
      role="img" 
      aria-labelledby="maps-ai-title maps-ai-desc"
      style={{ display: 'block', margin: '0 auto' }}
    >
      <title id="maps-ai-title">MAPS AI Scripting Assistant Logo</title>
      <desc id="maps-ai-desc">Robot chat bubble icon with classic TV antennas and balanced two-line title text.</desc>

      <defs>
        <linearGradient id="bubbleStroke" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1D4ED8"/>
          <stop offset="100%" stopColor="#0B1F6A"/>
        </linearGradient>
      </defs>

      <rect x="0" y="0" width="256" height="256" fill="none"/>

      {/* TV-style antennas */}
      <line x1="128" y1="72" x2="88" y2="40"
            stroke="url(#bubbleStroke)" strokeWidth="6" strokeLinecap="round"/>
      <circle cx="82" cy="34" r="8" fill="#1D4ED8"/>

      <line x1="128" y1="72" x2="168" y2="40"
            stroke="url(#bubbleStroke)" strokeWidth="6" strokeLinecap="round"/>
      <circle cx="174" cy="34" r="8" fill="#1D4ED8"/>

      {/* Chat bubble / robot head */}
      <path d="
        M 64 80
        H 192
        C 210 80 224 94 224 112
        V 138
        C 224 156 210 170 192 170
        H 122
        L 100 190
        L 100 170
        H 64
        C 46 170 32 156 32 138
        V 112
        C 32 94 46 80 64 80
        Z"
        fill="none"
        stroke="url(#bubbleStroke)"
        strokeWidth="10"
        strokeLinejoin="round"
      />

      {/* Eyes */}
      <circle cx="96" cy="125" r="14" fill="#1D4ED8"/>
      <circle cx="160" cy="125" r="14" fill="#1D4ED8"/>

      {showText && (
        <>
          {/* Title Line 1: MAPS AI */}
          <text x="50%" y="230"
                textAnchor="middle"
                fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
                fontSize="42"
                fontWeight="700"
                fill="#1D4ED8">
            MAPS AI
          </text>

          {/* Title Line 2: SCRIPTING ASSISTANT */}
          <text x="50%" y="248"
                textAnchor="middle"
                fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
                fontSize="14"
                fontWeight="700"
                letterSpacing="2.8"
                fill="#1D4ED8">
            SCRIPTING ASSISTANT
          </text>
        </>
      )}
    </svg>
  );
};

// File Icon Component (for non-image files)
const FileIcon = ({ file }) => {
  const getFileIcon = (fileType) => {
    const iconMap = {
      '.csv': 'table_chart',
      '.pdf': 'picture_as_pdf',
      '.txt': 'text_snippet',
      '.json': 'data_object',
      '.xml': 'code',
      '.html': 'html',
      '.py': 'code',
      '.js': 'code',
      '.jsx': 'code',
      '.ts': 'code',
      '.tsx': 'code',
      '.zip': 'folder_zip',
      '.tar': 'folder_zip',
      '.gz': 'folder_zip',
    };
    return iconMap[fileType] || 'description';
  };

  const handleDownload = (e) => {
    e.stopPropagation();
    const link = document.createElement('a');
    link.href = file.url;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="file-icon-item" onClick={handleDownload}>
      <div className="file-icon-wrapper">
        <span className="material-symbols-outlined file-icon">
          {getFileIcon(file.type)}
        </span>
      </div>
      <div className="file-icon-name">{file.name}</div>
      <span className="material-symbols-outlined download-icon">download</span>
    </div>
  );
};

// Image Viewer Modal Component with Pan/Zoom
const ImageViewerModal = ({ isOpen, image, onClose, isDark = false }) => {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Reset when image changes
  useEffect(() => {
    if (isOpen) {
      setScale(1);
      setPosition({ x: 0, y: 0 });
    }
  }, [isOpen, image]);

  if (!isOpen || !image) return null;

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setScale(s => Math.max(0.1, Math.min(5, s + delta)));
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  return (
    <div className="image-viewer-overlay" onClick={onClose} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}>
      <div className="image-viewer-container" onClick={(e) => e.stopPropagation()}>
        <div className="image-viewer-header">
          <div className="image-viewer-title">
            <span className="material-symbols-outlined" style={{fontSize: '20px'}}>image</span>
            <h3>{image.name}</h3>
          </div>
          <div className="viewer-controls">
            <button className="viewer-btn" onClick={() => setScale(s => Math.max(0.1, s - 0.25))} title="Zoom Out">
              <span className="material-symbols-outlined">zoom_out</span>
            </button>
            <span className="viewer-zoom-level">{Math.round(scale * 100)}%</span>
            <button className="viewer-btn" onClick={() => setScale(s => Math.min(5, s + 0.25))} title="Zoom In">
              <span className="material-symbols-outlined">zoom_in</span>
            </button>
            <button className="viewer-btn" onClick={handleReset} title="Reset View">
              <span className="material-symbols-outlined">center_focus_weak</span>
            </button>
          </div>
          <button className="viewer-close-btn" onClick={onClose} title="Close">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div 
          className="image-viewer-content"
          onMouseDown={handleMouseDown}
          onWheel={handleWheel}
          style={{
            background: isDark 
              ? '#1a1f2e' // Solid dark background for dark mode
              : '#f5f5f5'  // Light gray for light mode
          }}
        >
          <img 
            src={image.url}
            alt={image.name}
            style={{
              transform: `scale(${scale}) translate(${position.x / scale}px, ${position.y / scale}px)`,
              cursor: isDragging ? 'grabbing' : 'grab',
              transition: isDragging ? 'none' : 'transform 0.1s ease-out'
            }}
            draggable={false}
          />
        </div>
        <div className="image-viewer-footer">
          <span className="material-symbols-outlined" style={{fontSize: '16px'}}>info</span>
          <span>Use mouse wheel to zoom • Click and drag to pan</span>
        </div>
      </div>
    </div>
  );
};

// Library Selection Modal Component
const LibrarySelectionModal = ({ isOpen, onClose, onSelect, libraryImages }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content library-selection-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Select Image from Library</h2>
          <button className="modal-close" onClick={onClose}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className="modal-body library-selection-body">
          {libraryImages.length === 0 ? (
            <div className="empty-library-modal">
              <span className="material-symbols-outlined" style={{fontSize: '48px', color: '#ccc', marginBottom: '16px'}}>image</span>
              <p style={{color: '#999', fontSize: '14px'}}>No images in library. Upload an image first.</p>
            </div>
          ) : (
            <>
              {libraryImages.filter(img => img.user_id).length > 0 && (
                <div className="library-selection-section">
                  <div className="sidebar-separator">
                    <div className="separator-line"></div>
                    <div className="separator-label">Your Images</div>
                    <div className="separator-line"></div>
                  </div>
                  <div className="library-selection-grid">
                    {libraryImages.filter(img => img.user_id).map((image) => (
                      <div
                        key={image.id}
                        className="library-selection-card"
                        onClick={() => {
                          onSelect(image);
                          onClose();
                        }}
                      >
                        <div className="library-selection-image-wrapper">
                          <img src={image.url} alt={image.name} className="library-selection-image" />
                          <div className="library-selection-type-badge" style={{
                            backgroundColor: image.type === 'SEM'
                              ? '#1976d2'
                              : image.type === 'SDB'
                              ? '#388e3c'
                              : image.type === 'TEM'
                              ? '#f57c00'
                              : image.type === 'OPTICAL'
                              ? '#7b1fa2'
                              : '#666'
                          }}>
                            {image.type}
                          </div>
                        </div>
                        <div className="library-selection-card-content">
                          <h4>{image.name}</h4>
                          {image.description && <p>{image.description}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {libraryImages.filter(img => img.user_id).length > 0 && libraryImages.filter(img => !img.user_id).length > 0 && (
                <div className="sidebar-separator">
                  <div className="separator-line"></div>
                  <div className="separator-label">Library Images</div>
                  <div className="separator-line"></div>
                </div>
              )}
              
              {libraryImages.filter(img => !img.user_id).length > 0 && (
                <div className="library-selection-section">
                  {libraryImages.filter(img => img.user_id).length === 0 && (
                    <div className="sidebar-separator">
                      <div className="separator-line"></div>
                      <div className="separator-label">Images</div>
                      <div className="separator-line"></div>
                    </div>
                  )}
                  <div className="library-selection-grid">
                    {libraryImages.filter(img => !img.user_id).map((image) => (
                      <div
                        key={image.id}
                        className="library-selection-card"
                        onClick={() => {
                          onSelect(image);
                          onClose();
                        }}
                      >
                        <div className="library-selection-image-wrapper">
                          <img src={image.url} alt={image.name} className="library-selection-image" />
                          <div className="library-selection-type-badge" style={{
                            backgroundColor: image.type === 'SEM'
                              ? '#1976d2'
                              : image.type === 'SDB'
                              ? '#388e3c'
                              : image.type === 'TEM'
                              ? '#f57c00'
                              : image.type === 'OPTICAL'
                              ? '#7b1fa2'
                              : '#666'
                          }}>
                            {image.type}
                          </div>
                        </div>
                        <div className="library-selection-card-content">
                          <h4>{image.name}</h4>
                          {image.description && <p>{image.description}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// Upload Modal Component
const UploadModal = ({ isOpen, onClose, onUpload, currentUser }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [imageType, setImageType] = useState('SEM');
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [isDraggingModal, setIsDraggingModal] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      // Create preview URL
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
      // Auto-fill name from filename if name is empty
      if (!name.trim()) {
        const fileNameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, '');
        setName(fileNameWithoutExt);
      }
    }
  };
  
  const isImageFile = (file) => {
    // Check MIME type
    if (file.type && file.type.startsWith('image/')) {
      return true;
    }
    // Check file extension as fallback (for TIFF and other files that might not have proper MIME types)
    const extension = file.name.toLowerCase().match(/\.[^.]+$/);
    if (extension) {
      const imageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif', '.webp', '.ico'];
      return imageExtensions.includes(extension[0]);
    }
    return false;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingModal(false);
    
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => isImageFile(file));
    
    if (imageFile) {
      setFile(imageFile);
      // Create preview URL
      const url = URL.createObjectURL(imageFile);
      setPreviewUrl(url);
      // Auto-fill name from filename if name is empty
      if (!name.trim()) {
        const fileNameWithoutExt = imageFile.name.replace(/\.[^/.]+$/, '');
        setName(fileNameWithoutExt);
      }
      // Update file input
      if (fileInputRef.current) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(imageFile);
        fileInputRef.current.files = dataTransfer.files;
      }
    }
  };

  const handleUpload = async () => {
    if (!file || !name.trim()) {
      alert('Please provide a name and select an image file');
      return;
    }

    if (!currentUser) {
      alert('Please log in to upload images');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('image', file);
    formData.append('name', name);
    formData.append('description', description);
    formData.append('image_type', imageType);
    formData.append('user_id', currentUser.id);

    try {
      const response = await fetch('/library/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
      }

      const result = await response.json();
      onUpload(result);
      onClose();
      // Reset form
      setName('');
      setDescription('');
      setImageType('SEM');
      setFile(null);
      setPreviewUrl(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      alert('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  // Cleanup preview URL when modal closes or file changes
  React.useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className={`modal-content ${isDraggingModal ? 'drag-over' : ''}`}
        onClick={(e) => e.stopPropagation()}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDraggingModal(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (e.currentTarget === e.target || !e.currentTarget.contains(e.relatedTarget)) {
            setIsDraggingModal(false);
          }
        }}
        onDrop={handleDrop}
      >
        <div className="modal-header">
          <h2>Upload Image to Library</h2>
          <button className="modal-close" onClick={onClose}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>Image File *</label>
            <div 
              className={`file-upload-area ${isDraggingModal ? 'drag-over' : ''}`}
              onClick={() => fileInputRef.current?.click()}
            >
              {previewUrl ? (
                <div className="file-upload-preview">
                  <img src={previewUrl} alt="Preview" style={{maxWidth: '100%', maxHeight: '200px', borderRadius: '8px'}} />
                </div>
              ) : isDraggingModal ? (
                <div className="file-upload-drag-text">
                  <span className="material-symbols-outlined" style={{fontSize: '48px', color: '#1976d2', marginBottom: '8px'}}>cloud_upload</span>
                  <p style={{color: '#1976d2', fontWeight: '500'}}>Drop image here</p>
                </div>
              ) : (
                <div className="file-upload-drag-text">
                  <span className="material-symbols-outlined" style={{fontSize: '48px', color: '#999', marginBottom: '8px'}}>upload_file</span>
                  <p style={{color: '#666'}}>Click to select or drag and drop</p>
                  <p style={{color: '#999', fontSize: '12px', marginTop: '4px'}}>PNG, JPG, TIFF, GIF, etc.</p>
                </div>
              )}
              <input
                type="file"
                accept="image/*,.tiff,.tif"
                ref={fileInputRef}
                onChange={handleFileSelect}
                className="upload-modal-file-input"
                style={{ display: 'none' }}
              />
            </div>
            {file && <div className="file-preview-name">✓ {file.name}</div>}
          </div>
          <div className="form-group">
            <label>Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter image name"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter description (optional)"
              className="form-textarea"
              rows="3"
            />
          </div>
          <div className="form-group">
            <label>Image Type *</label>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  value="SEM"
                  checked={imageType === 'SEM'}
                  onChange={(e) => setImageType(e.target.value)}
                />
                <span>SEM</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  value="SDB"
                  checked={imageType === 'SDB'}
                  onChange={(e) => setImageType(e.target.value)}
                />
                <span>SDB</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  value="TEM"
                  checked={imageType === 'TEM'}
                  onChange={(e) => setImageType(e.target.value)}
                />
                <span>TEM</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  value="OPTICAL"
                  checked={imageType === 'OPTICAL'}
                  onChange={(e) => setImageType(e.target.value)}
                />
                <span>Optical</span>
              </label>
            </div>
          </div>
        </div>
        <div className="modal-footer">
          <button className="md-button md-button-outlined" onClick={onClose}>
            Cancel
          </button>
          <button
            className="md-button md-button-filled"
            onClick={handleUpload}
            disabled={uploading || !file || !name.trim()}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Library Image Card Component
const LibraryImageCard = ({ image, isSelected, onSelect, onDelete, onView }) => {
  const getTypeColor = (type) => {
    const colors = {
      'SEM': '#1976d2',
      'SDB': '#388e3c',
      'TEM': '#f57c00',
      'OPTICAL': '#7b1fa2'
    };
    return colors[type] || '#666';
  };

  const isUserImage = image.user_id != null;

  return (
    <div
      className={`library-image-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(image)}
    >
      <div className="library-card-image-wrapper">
        <img src={image.url} alt={image.name} className="library-card-image" />
        {isSelected && (
          <div className="library-card-overlay">
            <span className="material-symbols-outlined">check_circle</span>
          </div>
        )}
        {image.type && (
          <div className="library-card-type-badge" style={{ backgroundColor: getTypeColor(image.type) }}>
            {image.type}
          </div>
        )}
        <button
          className="library-card-view"
          onClick={(e) => {
            e.stopPropagation();
            onView(image);
          }}
          title="View image in full size"
        >
          <span className="material-symbols-outlined">zoom_in</span>
        </button>
      </div>
      <div className="library-card-content">
        <h4 className="library-card-title">{image.name}</h4>
        {image.description && (
          <p className="library-card-description">{image.description}</p>
        )}
      </div>
      {isUserImage && (
        <button
          className="library-card-delete"
          onClick={(e) => {
            e.stopPropagation();
            if (window.confirm(`Delete "${image.name}"?`)) {
              onDelete(image.id);
            }
          }}
        >
          <span className="material-symbols-outlined">delete</span>
        </button>
      )}
    </div>
  );
};

// Thumbnail Component (for images)
const Thumbnail = ({ file, isSelected, onClick, onView }) => {
  const isImage = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(file.type);
  
  if (!isImage) {
    return null;
  }

  return (
    <div 
      className={`thumbnail-item ${isSelected ? 'selected' : ''}`}
      onClick={() => onClick(file.url)}
    >
      <div className="thumbnail-wrapper">
        <img src={file.url} alt={file.name} className="thumbnail-image" />
        {isSelected && (
          <div className="thumbnail-overlay">
            <span className="material-symbols-outlined">check_circle</span>
          </div>
        )}
        {onView && (
          <button
            className="thumbnail-view-button"
            onClick={(e) => {
              e.stopPropagation();
              onView(file);
            }}
            title="View image in full size"
          >
            <span className="material-symbols-outlined">zoom_in</span>
          </button>
        )}
      </div>
      <div className="thumbnail-label">{file.name}</div>
    </div>
  );
};

// Pan/Zoom Image Viewer Component
const ImageViewer = ({ src, alt, title, isDark = false }) => {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [fitScale, setFitScale] = useState(1);
  const containerRef = useRef(null);
  const imageRef = useRef(null);
  const isInitialLoadRef = useRef(true);

  // Calculate fit-to-view scale only on initial load
  useEffect(() => {
    const calculateFitScale = () => {
      if (imageRef.current && containerRef.current && isInitialLoadRef.current) {
        const container = containerRef.current.getBoundingClientRect();
        const image = imageRef.current;
        
        // Get natural image dimensions
        const imgWidth = image.naturalWidth;
        const imgHeight = image.naturalHeight;
        
        if (imgWidth === 0 || imgHeight === 0) return; // Image not loaded yet
        
        // Get container dimensions (with minimal padding)
        const containerWidth = container.width - 20;
        const containerHeight = container.height - 20;
        
        // Calculate scale to fit (allow scaling up or down)
        const scaleX = containerWidth / imgWidth;
        const scaleY = containerHeight / imgHeight;
        const newFitScale = Math.min(scaleX, scaleY); // Use the smaller scale to fit
        
        setFitScale(newFitScale);
        setScale(newFitScale);
        setPosition({ x: 0, y: 0 });
        
        // Mark that initial load is complete
        isInitialLoadRef.current = false;
      }
    };

    const img = imageRef.current;
    if (img) {
      if (img.complete && img.naturalWidth > 0) {
        calculateFitScale();
      } else {
        img.addEventListener('load', calculateFitScale);
        return () => img.removeEventListener('load', calculateFitScale);
      }
    }
  }, [src]);

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 5));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, Math.min(fitScale, 0.5)));
  };

  const handleReset = () => {
    setScale(fitScale);
    setPosition({ x: 0, y: 0 });
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setScale(prev => Math.max(Math.min(fitScale, 0.5), Math.min(5, prev + delta)));
  };

  const handleMouseDown = (e) => {
    if (scale > 1) {
      e.preventDefault();
      setIsDragging(true);
      setDragStart({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
    }
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isDragging && scale > 1) {
        setPosition({
          x: e.clientX - dragStart.x,
          y: e.clientY - dragStart.y
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart, scale]);

  return (
    <div className="image-viewer-container">
      <div className="image-viewer-header">
        <h4>{title}</h4>
        <div className="image-viewer-controls">
          <button className="zoom-btn" onClick={handleZoomOut} disabled={scale <= Math.min(fitScale, 0.5)}>
            <span className="material-symbols-outlined">remove</span>
          </button>
          <span className="zoom-level">{Math.round(scale * 100)}%</span>
          <button className="zoom-btn" onClick={handleZoomIn} disabled={scale >= 5}>
            <span className="material-symbols-outlined">add</span>
          </button>
          <button className="zoom-btn" onClick={handleReset}>
            <span className="material-symbols-outlined">refresh</span>
          </button>
        </div>
      </div>
      <div 
        className="image-viewer-wrapper"
        ref={containerRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        style={{ 
          cursor: scale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
          background: isDark ? '#1a1f2e' : '#f5f5f5'
        }}
      >
        <img
          ref={imageRef}
          src={src}
          alt={alt}
          className="zoomable-image"
          style={{
            transform: `scale(${scale}) translate(${position.x / scale}px, ${position.y / scale}px)`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out'
          }}
          draggable={false}
        />
      </div>
    </div>
  );
};

// Login Screen Component
const LoginScreen = ({ onLogin }) => {
  const [users, setUsers] = useState([]);
  const [newUserName, setNewUserName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await fetch('/api/users');
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectUser = (user) => {
    localStorage.setItem('currentUser', JSON.stringify(user));
    onLogin(user);
  };

  const handleCreateUser = async () => {
    if (!newUserName.trim()) {
      alert('Please enter a name');
      return;
    }

    setIsCreating(true);
    try {
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newUserName.trim() })
      });

      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.error('Non-JSON response:', text);
        alert(`Failed to create user: ${response.status} ${response.statusText}\n\n${text.substring(0, 200)}`);
        setIsCreating(false);
        return;
      }

      if (response.ok && data.success) {
        localStorage.setItem('currentUser', JSON.stringify(data.user));
        onLogin(data.user);
        setNewUserName('');
      } else {
        console.error('Error response:', data);
        alert(data.error || 'Failed to create user');
      }
    } catch (error) {
      console.error('Failed to create user:', error);
      const errorMsg = error && error.message ? error.message : String(error || 'Network error');
      alert(`Failed to create user: ${errorMsg}`);
    } finally {
      setIsCreating(false);
    }
  };

  // Filter users based on search query
  const filteredUsers = users.filter(user => 
    user.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: `
        radial-gradient(ellipse at 70% 50%, rgba(0, 191, 255, 0.4) 0%, transparent 50%),
        radial-gradient(ellipse at 30% 70%, rgba(72, 209, 204, 0.3) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 30%, rgba(30, 144, 255, 0.3) 0%, transparent 50%),
        linear-gradient(180deg, #001a33 0%, #003d5c 30%, #00334d 70%, #001f33 100%)
      `,
      backgroundSize: '100% 100%, 100% 100%, 100% 100%, 100% 100%',
      animation: 'auroraFlow 20s ease-in-out infinite',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div className="login-container" style={{
        background: '#f0f4f8',
        borderRadius: '16px',
        padding: '40px',
        maxWidth: '1000px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(0, 191, 255, 0.2)',
        display: 'flex',
        gap: '40px'
      }}>
        {/* Left Column: Logo, Description, Create Account */}
        <div style={{
          flex: '1',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <div style={{ marginBottom: '24px' }}>
              <MapsAILogo size={180} showText={true} />
            </div>
            <h1 style={{ margin: '0 0 8px 0', fontSize: '32px', fontWeight: '700', color: '#333', letterSpacing: '-0.5px' }}>
              Maps Script Helper
            </h1>
            <p style={{ margin: '0 0 16px 0', color: '#00BFFF', fontSize: '14px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              AI-Powered Python Script Generator
            </p>
            <p style={{ margin: '0', color: '#666', fontSize: '16px', lineHeight: '1.6' }}>
              Select your account or create a new one to get started with AI-powered Python scripting for MAPS.
            </p>
          </div>

          {/* Create New Account Section */}
          <div style={{
            padding: '24px',
            background: 'white',
            borderRadius: '12px',
            border: '2px solid #e0e0e0'
          }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#333' }}>
              Create New Account
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <input
                type="text"
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateUser();
                  }
                }}
                placeholder="Enter your name"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none',
                  boxSizing: 'border-box',
                  transition: 'border-color 0.2s'
                }}
                onFocus={(e) => {
                  e.currentTarget.borderColor = '#667eea';
                }}
                onBlur={(e) => {
                  e.currentTarget.borderColor = '#e0e0e0';
                }}
              />
              <button
                onClick={handleCreateUser}
                disabled={isCreating || !newUserName.trim()}
                style={{
                  width: '100%',
                  padding: '12px 24px',
                  background: isCreating || !newUserName.trim() ? '#ccc' : '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: isCreating || !newUserName.trim() ? 'not-allowed' : 'pointer',
                  transition: 'background 0.2s'
                }}
              >
                {isCreating ? 'Creating...' : 'Create Account'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: User List */}
        <div style={{
          flex: '1',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
              <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#999', animation: 'spin 1s linear infinite' }}>
                refresh
              </span>
            </div>
          ) : (
            <>
              {users.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <h2 style={{ fontSize: '18px', fontWeight: '600', margin: 0, color: '#333' }}>
                      Select Account
                    </h2>
                    <span style={{ fontSize: '14px', color: '#666' }}>
                      {filteredUsers.length} {filteredUsers.length === 1 ? 'user' : 'users'}
                      {searchQuery && ` (of ${users.length})`}
                    </span>
                  </div>
                  
                  {/* Search Input */}
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ position: 'relative' }}>
                      <span className="material-symbols-outlined" style={{
                        position: 'absolute',
                        left: '12px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        fontSize: '20px',
                        color: '#999',
                        pointerEvents: 'none'
                      }}>
                        search
                      </span>
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search users..."
                        style={{
                          width: '100%',
                          padding: '10px 12px 10px 40px',
                          border: '2px solid #e0e0e0',
                          borderRadius: '8px',
                          fontSize: '14px',
                          outline: 'none',
                          transition: 'border-color 0.2s',
                          boxSizing: 'border-box'
                        }}
                        onFocus={(e) => {
                          e.currentTarget.borderColor = '#667eea';
                        }}
                        onBlur={(e) => {
                          e.currentTarget.borderColor = '#e0e0e0';
                        }}
                      />
                      {searchQuery && (
                        <button
                          onClick={() => setSearchQuery('')}
                          style={{
                            position: 'absolute',
                            right: '8px',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            borderRadius: '4px'
                          }}
                          onMouseOver={(e) => {
                            e.currentTarget.background = '#f0f0f0';
                          }}
                          onMouseOut={(e) => {
                            e.currentTarget.background = 'transparent';
                          }}
                        >
                          <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#999' }}>
                            close
                          </span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Scrollable User List */}
                  {filteredUsers.length > 0 ? (
                    <div 
                      className="login-user-list"
                      style={{
                        flex: 1,
                        minHeight: '400px',
                        maxHeight: '500px',
                        overflowY: 'auto',
                        overflowX: 'hidden',
                        border: '2px solid #e0e0e0',
                        borderRadius: '8px',
                        padding: '8px',
                        background: 'white'
                      }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {filteredUsers.map((user) => (
                          <button
                            key={user.id}
                            onClick={() => handleSelectUser(user)}
                            style={{
                              padding: '12px 16px',
                              border: '2px solid #e0e0e0',
                              borderRadius: '6px',
                              background: 'white',
                              cursor: 'pointer',
                              textAlign: 'left',
                              fontSize: '15px',
                              fontWeight: '500',
                              color: '#333',
                              transition: 'all 0.2s',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '12px',
                              width: '100%'
                            }}
                            onMouseOver={(e) => {
                              e.currentTarget.style.borderColor = '#667eea';
                              e.currentTarget.style.background = '#f5f7ff';
                            }}
                            onMouseOut={(e) => {
                              e.currentTarget.style.borderColor = '#e0e0e0';
                              e.currentTarget.style.background = 'white';
                            }}
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: '22px', color: '#667eea', flexShrink: 0 }}>
                              person
                            </span>
                            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {user.name}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div style={{
                      flex: 1,
                      minHeight: '400px',
                      padding: '32px',
                      textAlign: 'center',
                      border: '2px solid #e0e0e0',
                      borderRadius: '8px',
                      background: 'white',
                      color: '#999',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '48px', marginBottom: '8px' }}>
                        person_off
                      </span>
                      <p style={{ margin: 0, fontSize: '14px' }}>
                        No users found matching "{searchQuery}"
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{
                  padding: '40px',
                  textAlign: 'center',
                  color: '#666',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flex: 1
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '64px', marginBottom: '16px', color: '#999' }}>
                    group
                  </span>
                  <p style={{ margin: 0, fontSize: '16px' }}>
                    No existing users. Create your account on the left to get started!
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes auroraFlow {
          0% {
            background: 
              radial-gradient(ellipse at 70% 50%, rgba(0, 191, 255, 0.4) 0%, transparent 50%),
              radial-gradient(ellipse at 30% 70%, rgba(72, 209, 204, 0.3) 0%, transparent 50%),
              radial-gradient(ellipse at 50% 30%, rgba(30, 144, 255, 0.3) 0%, transparent 50%),
              linear-gradient(180deg, #001a33 0%, #003d5c 30%, #00334d 70%, #001f33 100%);
          }
          25% {
            background: 
              radial-gradient(ellipse at 60% 60%, rgba(0, 191, 255, 0.5) 0%, transparent 50%),
              radial-gradient(ellipse at 40% 50%, rgba(72, 209, 204, 0.4) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 40%, rgba(30, 144, 255, 0.3) 0%, transparent 50%),
              linear-gradient(180deg, #001a33 0%, #003d5c 30%, #00334d 70%, #001f33 100%);
          }
          50% {
            background: 
              radial-gradient(ellipse at 50% 70%, rgba(0, 191, 255, 0.4) 0%, transparent 50%),
              radial-gradient(ellipse at 60% 40%, rgba(72, 209, 204, 0.35) 0%, transparent 50%),
              radial-gradient(ellipse at 40% 60%, rgba(30, 144, 255, 0.3) 0%, transparent 50%),
              linear-gradient(180deg, #001a33 0%, #003d5c 30%, #00334d 70%, #001f33 100%);
          }
          75% {
            background: 
              radial-gradient(ellipse at 40% 50%, rgba(0, 191, 255, 0.45) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 60%, rgba(72, 209, 204, 0.3) 0%, transparent 50%),
              radial-gradient(ellipse at 50% 50%, rgba(30, 144, 255, 0.35) 0%, transparent 50%),
              linear-gradient(180deg, #001a33 0%, #003d5c 30%, #00334d 70%, #001f33 100%);
          }
          100% {
            background: 
              radial-gradient(ellipse at 70% 50%, rgba(0, 191, 255, 0.4) 0%, transparent 50%),
              radial-gradient(ellipse at 30% 70%, rgba(72, 209, 204, 0.3) 0%, transparent 50%),
              radial-gradient(ellipse at 50% 30%, rgba(30, 144, 255, 0.3) 0%, transparent 50%),
              linear-gradient(180deg, #001a33 0%, #003d5c 30%, #00334d 70%, #001f33 100%);
          }
        }
      `}</style>
    </div>
  );
};

const App = () => {
  // Welcome message shown on initial load
  const WELCOME_MESSAGE = `# Welcome to Maps Python Script Helper! 🗺️

# Getting Started:
# 1. Browse "Default Templates" in the Scripts tab
# 2. Click on a template to load it here
# 3. Select an image from the Image Library
# 4. Click "Run" to execute your script
# 5. Save your modified scripts to "My Scripts"

# Your Python code will be executed in a sandboxed Docker container
# with access to libraries like PIL, NumPy, OpenCV, scikit-image, and more.

# Example: Simple image processing
import MapsBridge
from PIL import Image
import numpy as np

def main():
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    # Your code here...
    MapsBridge.LogInfo("Hello from Maps!")

if __name__ == "__main__":
    main()
`;

  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('welcome'); // Start at welcome screen
  const [code, setCode] = useState(WELCOME_MESSAGE);
  const [editorKey, setEditorKey] = useState(0); // Force editor recreation
  const [output, setOutput] = useState('Ready.');
  const [lastError, setLastError] = useState(null); // Store last execution error for AI context
  const [consecutiveFailures, setConsecutiveFailures] = useState(0); // Track consecutive failures for verbose debugging
  const [originalImage, setOriginalImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [outputFiles, setOutputFiles] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [allFiles, setAllFiles] = useState([]);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [libraryImages, setLibraryImages] = useState([]);
  const [selectedLibraryImage, setSelectedLibraryImage] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showLibrarySelectionModal, setShowLibrarySelectionModal] = useState(false);
  const [consoleExpanded, setConsoleExpanded] = useState(false);
  const [consoleHeight, setConsoleHeight] = useState(200); // Default height in pixels
  const [isResizingConsole, setIsResizingConsole] = useState(false);
  const [showImageViewer, setShowImageViewer] = useState(false);
  const [viewerImage, setViewerImage] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [userId, setUserId] = useState(null);
  const [backendVersion, setBackendVersion] = useState(null);
  const [assistantWidth, setAssistantWidth] = useState(360); // Default width in pixels
  const [isResizing, setIsResizing] = useState(false);
  const [isCodeUpdating, setIsCodeUpdating] = useState(false); // Track code update animation
  const [aiModel, setAiModel] = useState('gemini-2.5-flash-lite'); // Always default to flash-lite
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [isSaveAsMode, setIsSaveAsMode] = useState(false); // Track if doing "Save As" (always create new)
  const [scriptName, setScriptName] = useState('');
  const [scriptDescription, setScriptDescription] = useState('');
  const [userScripts, setUserScripts] = useState([]);
  const [libraryScripts, setLibraryScripts] = useState([]); // Library scripts from database
  const [scriptsSubTab, setScriptsSubTab] = useState('templates'); // 'templates' or 'user'
  const [currentScript, setCurrentScript] = useState(null); // Track currently loaded script for updates
  const [toast, setToast] = useState(null); // Toast notification state
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(false); // Track left panel collapsed state
  const [theme, setTheme] = useState('light'); // Theme: 'light' or 'dark'

  const isDark = theme === 'dark';

  // Load current user from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      try {
        const user = JSON.parse(savedUser);
        console.log('[MapsScriptHelper] Loading user from localStorage, setting activeTab to welcome');
        // Clear AI + workspace state (same behavior as "New Chat")
        setMessages([]);
        setAiModel('gemini-2.5-flash-lite');
        setLastError(null);
        setOutput('Ready.');
        setOriginalImage(null);
        setResultImage(null);
        setOutputFiles([]);
        setSelectedImage(null);
        setSelectedLibraryImage(null);
        setUploadedFile(null);
        setShowUploadModal(false);
        setShowLibrarySelectionModal(false);
        setShowImageViewer(false);
        setViewerImage(null);
        if (monacoEditorRef.current) {
          monacoEditorRef.current.setValue('');
        }

        setCurrentUser(user);
        setUserId(user.id);
        // Always start on welcome screen when loading from localStorage
        setActiveTab('welcome');
        setCode(''); // Clear code to show welcome screen
        setCurrentScript(null);
      } catch (e) {
        console.error('Failed to parse saved user:', e);
        localStorage.removeItem('currentUser');
      }
    }
  }, []);

  const handleLogin = (user) => {
    console.log('[MapsScriptHelper] Logging in user, setting activeTab to welcome');
    // Clear AI + workspace state (same behavior as "New Chat")
    setMessages([]);
    setAiModel('gemini-2.5-flash-lite');
    setLastError(null);
    setOutput('Ready.');
    setOriginalImage(null);
    setResultImage(null);
    setOutputFiles([]);
    setSelectedImage(null);
    setSelectedLibraryImage(null);
    setUploadedFile(null);
    setShowUploadModal(false);
    setShowLibrarySelectionModal(false);
    setShowImageViewer(false);
    setViewerImage(null);

    // Dispose Monaco editor to force recreation with welcome message
    if (monacoEditorRef.current) {
      monacoEditorRef.current.dispose();
      monacoEditorRef.current = null;
    }
    
    setCurrentUser(user);
    setUserId(user.id);
    // Always start on the welcome screen when logging in
    setActiveTab('welcome');
    setCode(''); // Clear code to show welcome screen
    setCurrentScript(null); // Clear any loaded script
    setEditorKey(prev => prev + 1); // Force editor recreation
  };

  const handleLogout = () => {
    console.log('[MapsScriptHelper] Logging out, setting activeTab to welcome');
    // Dispose Monaco editor to force recreation with welcome message
    if (monacoEditorRef.current) {
      monacoEditorRef.current.dispose();
      monacoEditorRef.current = null;
    }
    
    localStorage.removeItem('currentUser');
    setCurrentUser(null);
    setUserId(null);
    // Clear user-specific data
    setUserScripts([]);
    setLibraryImages([]);
    setSelectedLibraryImage(null);
    // Reset to welcome screen
    setActiveTab('welcome');
    setCode(''); // Clear code to show welcome screen
    setCurrentScript(null);
    setEditorKey(prev => prev + 1); // Force editor recreation
  };

  const handleResetAllUserData = async () => {
    if (!confirm('⚠️ RESET ALL USER DATA?\n\nThis will permanently delete:\n• All user accounts\n• All saved scripts (user-created)\n• All uploaded images (user-uploaded)\n\nDefault templates and library images will be kept.\n\nThis action CANNOT be undone!\n\nAre you absolutely sure?')) {
      return;
    }
    
    try {
      const response = await fetch('/api/admin/reset-user-data', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        showToast(`Reset complete: ${data.deleted.users} users, ${data.deleted.scripts} scripts, ${data.deleted.images} images deleted`, 'success');
        // Log out the current user
        localStorage.removeItem('currentUser');
        setCurrentUser(null);
        setUserId(null);
        setUserScripts([]);
        setLibraryImages([]);
        setSelectedLibraryImage(null);
      } else {
        showToast('Failed to reset data: ' + (data.error || 'Unknown error'), 'error');
      }
    } catch (error) {
      showToast('Failed to reset data: ' + error.message, 'error');
    }
  };
  
  // Example scripts for the My Scripts tab
  // Library scripts are now loaded from database API
  // See loadLibraryScripts() function below
  const exampleScripts = libraryScripts; // Use library scripts from database
  
  // Legacy hardcoded scripts (keeping for reference/fallback)
  const legacyExampleScripts = [
    {
      id: 'thermal-colormap',
      name: 'Thermal Colormap',
      description: 'Applies a thermal/hot false-color visualization (black → red → yellow → white) using multi-channel output.',
      category: 'Visualization',
      code: `# MAPS Script Bridge Example - False Color (Multi-Channel)
# Outputs separate R/G/B intensity channels for thermal colormap

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np

def get_thermal_channels(gray_array):
    """
    Generate thermal colormap as separate intensity channels.
    Black -> Red -> Yellow -> White
    Returns: (red_intensity, green_intensity, blue_intensity) as uint8 arrays
    """
    normalized = gray_array.astype(np.float32) / 255.0
    
    # Each channel is a grayscale intensity map
    r = np.clip(3.0 * normalized, 0, 1)
    g = np.clip(3.0 * normalized - 1.0, 0, 1)
    b = np.clip(3.0 * normalized - 2.0, 0, 1)
    
    return (
        (r * 255).astype(np.uint8),
        (g * 255).astype(np.uint8),
        (b * 255).astype(np.uint8)
    )

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    gray_array = np.array(img)
    
    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Generate thermal colormap channels
    red_intensity, green_intensity, blue_intensity = get_thermal_channels(gray_array)
    
    # 4. Save each channel to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "thermal_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    
    red_path = os.path.join(output_folder, f"{base}_red.png")
    green_path = os.path.join(output_folder, f"{base}_green.png")
    blue_path = os.path.join(output_folder, f"{base}_blue.png")
    
    Image.fromarray(red_intensity, mode="L").save(red_path)
    Image.fromarray(green_intensity, mode="L").save(green_path)
    Image.fromarray(blue_intensity, mode="L").save(blue_path)
    
    # 5. Create output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Thermal " + sourceTileSet.Name, 
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 6. Create channels with their display colors (additive blending)
    MapsBridge.CreateChannel("Red", (255, 0, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Green", (0, 255, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Blue", (0, 0, 255), True, outputTileSet.Guid)
    
    # 7. Send each intensity map to its channel
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Red", red_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Green", green_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Blue", blue_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] processed\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()`
    },
    {
      id: 'brightness-threshold',
      name: 'Brightness Threshold',
      description: 'Highlights pixels above a brightness threshold. Uses ScriptParameters for the threshold value.',
      category: 'Analysis',
      code: `# MAPS Script Bridge - Brightness Threshold
# Highlights pixels above a configurable threshold

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # Get threshold from script parameters (default: 128)
    try:
        threshold = float(request.ScriptParameters) if request.ScriptParameters else 128
    except ValueError:
        threshold = 128
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    
    MapsBridge.LogInfo(f"Loaded: {input_filename}, Threshold: {threshold}")
    
    # 3. Apply threshold - pixels above threshold become white, below become black
    result = img.point(lambda p: 255 if p > threshold else 0)
    
    # 4. Save to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "threshold_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_threshold.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Threshold " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Highlight", (255, 0, 0), True, outputTileSet.Guid)
    
    # 6. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Highlight", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] threshold={threshold}\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()`
    },
    {
      id: 'edge-detection',
      name: 'Edge Detection',
      description: 'Detects edges in the image using Sobel operator for feature highlighting.',
      category: 'Analysis',
      code: `# MAPS Script Bridge - Edge Detection
# Detects edges using Sobel operator

import os
import tempfile
import MapsBridge
from PIL import Image, ImageFilter
import numpy as np

def sobel_edge_detection(img_array):
    """Apply Sobel edge detection"""
    from scipy import ndimage
    
    # Sobel kernels
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    
    # Apply convolution
    gx = ndimage.convolve(img_array.astype(float), sobel_x)
    gy = ndimage.convolve(img_array.astype(float), sobel_y)
    
    # Compute magnitude
    magnitude = np.sqrt(gx**2 + gy**2)
    
    # Normalize to 0-255
    magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
    return magnitude

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img)
    
    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Apply edge detection
    edges = sobel_edge_detection(img_array)
    result = Image.fromarray(edges, mode="L")
    
    # 4. Save to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "edge_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_edges.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Edges " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Edges", (0, 255, 255), True, outputTileSet.Guid)
    
    # 6. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Edges", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] edge detection\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()`
    },
    {
      id: 'copy-original',
      name: 'Copy Original',
      description: 'Simple script that copies the original image to output. Good starting template.',
      category: 'Template',
      code: `# MAPS Script Bridge - Copy Original
# Simple template that copies the input image to output

import os
import shutil
import tempfile
import MapsBridge

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Get input path
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    
    MapsBridge.LogInfo(f"Processing: {input_filename}")
    
    # 3. Copy to temp folder (save as PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "copy_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    
    # Use PNG extension for output (works in both helper app and MAPS)
    output_path = os.path.join(output_folder, f"{base}_copy.png")
    
    # Open and re-save as PNG to ensure compatibility
    from PIL import Image
    img = Image.open(input_path)
    img.save(output_path)
    
    # 4. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Copy " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Original", (255, 255, 255), True, outputTileSet.Guid)
    
    # 5. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Original", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()`
    },
    {
      id: 'particle-categorization',
      name: 'Particle Categorization',
      description: 'Segments particles, measures shape (area, solidity, circularity), and categorizes as round/irregular/small with color-coded output.',
      category: 'Segmentation',
      code: `# MAPS Script Bridge - Particle Categorization
# Segments particles in EM images, measures shape, and categorizes them.
# Outputs:
#   1) Grayscale mask (labels per particle)
#   2) RGB visualization colored by category (round / irregular / small)

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
from scipy import ndimage
from skimage import filters, morphology, measure, exposure

# ============================================================================
# TUNABLE PARAMETERS - Adjust for your specific images
# ============================================================================

GAUSSIAN_SIGMA = 1.5          # Noise reduction blur
CLAHE_CLIP_LIMIT = 0.03       # Contrast enhancement
MIN_PARTICLE_SIZE = 50        # Minimum particle area in pixels
FILL_HOLES = True             # Fill holes inside particles

# In this image, particles are BRIGHT on a DARK background
PARTICLES_ARE_DARK = False

# ---- Categorization thresholds ---------------------------------------------

# Anything smaller than this (in pixels) is "small"
SMALL_AREA_THRESHOLD = 300

# Shape thresholds for "round" particles
MIN_SOLIDITY_ROUND = 0.95     # 0-1, higher = fewer concavities
MIN_CIRCULARITY_ROUND = 0.85  # 4*pi*A / P^2, 1 = perfect circle

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_image(img_array):
    """Normalize image intensities to 0-1 range."""
    img_float = img_array.astype(np.float64)
    img_min, img_max = img_float.min(), img_float.max()
    if img_max - img_min > 0:
        return (img_float - img_min) / (img_max - img_min)
    return img_float

def preprocess_image(img_array, sigma=GAUSSIAN_SIGMA, clip_limit=CLAHE_CLIP_LIMIT):
    """Apply Gaussian blur and CLAHE contrast enhancement."""
    blurred = ndimage.gaussian_filter(img_array, sigma=sigma)
    blurred_norm = normalize_image(blurred)
    enhanced = exposure.equalize_adapthist(blurred_norm, clip_limit=clip_limit)
    return (enhanced * 255).astype(np.uint8)

def segment_particles(
    img_array,
    min_size=MIN_PARTICLE_SIZE,
    fill_holes=FILL_HOLES,
    dark_particles=PARTICLES_ARE_DARK
):
    """
    Segment particles using Otsu thresholding.
    Returns labeled image where each particle has a unique integer ID.
    """
    threshold = filters.threshold_otsu(img_array)

    if dark_particles:
        binary = img_array < threshold
    else:
        binary = img_array > threshold

    if fill_holes:
        binary = ndimage.binary_fill_holes(binary)

    binary = morphology.remove_small_objects(binary, min_size=min_size)
    labeled, num_particles = ndimage.label(binary)
    return labeled, num_particles

def categorize_particles(labeled_array):
    """
    For each labeled particle, compute region properties and assign a category:
      1 = round
      2 = irregular
      3 = small
    Returns:
      category_map: 2D array with category IDs
      stats: list of per-particle dictionaries with measurements & category
    """
    props = measure.regionprops(labeled_array)
    category_map = np.zeros_like(labeled_array, dtype=np.uint8)
    stats = []

    for region in props:
        label = region.label
        area = region.area
        solidity = region.solidity

        perimeter = region.perimeter if region.perimeter > 0 else 1.0
        circularity = 4.0 * np.pi * area / (perimeter ** 2)

        # Decide category
        if area < SMALL_AREA_THRESHOLD:
            category = 3  # small
        elif (solidity >= MIN_SOLIDITY_ROUND) and (circularity >= MIN_CIRCULARITY_ROUND):
            category = 1  # round
        else:
            category = 2  # irregular

        category_map[labeled_array == label] = category

        stats.append({
            "label": label,
            "area": float(area),
            "solidity": float(solidity),
            "circularity": float(circularity),
            "category": int(category),
        })

    return category_map, stats

def make_category_rgb(category_map):
    """
    Convert category map to RGB for visualization:
      0 = background (black)
      1 = round      (green)
      2 = irregular  (red)
      3 = small      (blue)
    """
    h, w = category_map.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    color_round = (0, 255, 0)
    color_irregular = (255, 0, 0)
    color_small = (0, 0, 255)

    rgb[category_map == 1] = color_round
    rgb[category_map == 2] = color_irregular
    rgb[category_map == 3] = color_small

    return rgb

# ============================================================================
# MAIN
# ============================================================================

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]

    # 2. Load the input image (grayscale)
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img)

    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")

    # 3. Preprocess: blur + CLAHE
    preprocessed = preprocess_image(img_array)
    MapsBridge.LogInfo("Preprocessing complete (Gaussian blur + CLAHE)")

    # 4. Segment particles
    labeled, num_particles = segment_particles(preprocessed)
    MapsBridge.LogInfo(f"Segmentation complete: {num_particles} particles found")

    # 5. Categorize particles
    category_map, stats = categorize_particles(labeled)

    # Count categories
    n_round = sum(s["category"] == 1 for s in stats)
    n_irregular = sum(s["category"] == 2 for s in stats)
    n_small = sum(s["category"] == 3 for s in stats)
    MapsBridge.LogInfo(
        f"Categories: {n_round} round, {n_irregular} irregular, {n_small} small"
    )

    # 6. Build visualization RGB
    category_rgb = make_category_rgb(category_map)

    # 7. Setup output folder
    output_folder = os.path.join(tempfile.gettempdir(), "segmentation_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)

    # Use PNG for outputs
    mask_path = os.path.join(output_folder, f"{base}_labels.png")
    cat_path = os.path.join(output_folder, f"{base}_categories.png")

    # 8. Save labeled mask (16-bit-style visualization)
    if labeled.max() > 0:
        mask_visual = (
            labeled.astype(np.float32) / labeled.max() * 255
        ).astype(np.uint8)
    else:
        mask_visual = labeled.astype(np.uint8)

    mask_img = Image.fromarray(mask_visual, mode="L")
    mask_img.save(mask_path)
    MapsBridge.LogInfo(f"Saved mask: {os.path.basename(mask_path)}")

    # 9. Save category RGB image
    cat_img = Image.fromarray(category_rgb, mode="RGB")
    cat_img.save(cat_path)
    MapsBridge.LogInfo(f"Saved categories: {os.path.basename(cat_path)}")

    # 10. Create output tile set in MAPS
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Particle Categories " + sourceTileSet.Name,
        targetLayerGroupName="Outputs",
    )
    outputTileSet = outputTileSetInfo.TileSet

    # 11. Create channels and send outputs
    MapsBridge.CreateChannel("Labels", (255, 255, 255), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Categories", (255, 255, 255), True, outputTileSet.Guid)

    MapsBridge.SendSingleTileOutput(
        tileInfo.Row,
        tileInfo.Column,
        "Labels",
        mask_path,
        True,
        outputTileSet.Guid,
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row,
        tileInfo.Column,
        "Categories",
        cat_path,
        True,
        outputTileSet.Guid,
    )

    # 12. Append notes (summary counts)
    MapsBridge.AppendNotes(
        (
            f"Tile [{tileInfo.Column}, {tileInfo.Row}]: "
            f"{num_particles} particles "
            f"({n_round} round, {n_irregular} irregular, {n_small} small)\\n"
        ),
        outputTileSet.Guid,
    )
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()`
    },
    {
      id: 'false-color-single-image',
      name: 'False Color - Single Image',
      description: 'Creates a single RGB false-color visualization using viridis colormap. Good for quick viewing, but no independent channel control in Maps.',
      category: 'Visualization',
      code: `# MAPS Script Bridge - False Color (Single Image)
# Creates a single RGB color visualization using the viridis colormap.
# Output: One color image (no independent channel control in Maps)
# Use when: You want a quick color visualization or final composite

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib.cm as cm

def main():
    # 1. Get the script request from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Get input image filename for channel "0"
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    
    # 3. Load the image and convert to grayscale, then to NumPy array
    MapsBridge.LogInfo(f"Loading: {input_path}")
    img = Image.open(input_path).convert("L")  # Convert to grayscale
    gray_data = np.array(img)
    
    # 4. Apply the false color map
    # Normalize the grayscale data to the 0.0-1.0 range
    # This automatically handles both 8-bit and 16-bit images
    MapsBridge.LogInfo("Applying 'viridis' colormap...")
    min_val = gray_data.min()
    max_val = gray_data.max()
    
    if max_val > min_val:
        normalized_data = (gray_data - min_val) / (max_val - min_val)
    else:
        # Handle solid color images to avoid division by zero
        normalized_data = np.zeros_like(gray_data, dtype=float)

    # Apply the 'viridis' colormap. The result is an RGBA array with float values.
    colored_data = cm.viridis(normalized_data)
    
    # Convert from float RGBA (0.0-1.0) to uint8 RGB (0-255) for saving
    rgb_array = (colored_data[:, :, :3] * 255).astype(np.uint8)
    
    # Convert the NumPy array back to a PIL Image
    result_image = Image.fromarray(rgb_array)

    # 5. Save output to a temporary folder
    output_folder = os.path.join(tempfile.gettempdir(), "false_color_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_color.png")
    result_image.save(output_path)
    MapsBridge.LogInfo(f"Saved false color image to: {output_path}")
    
    # 6. Create the output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "False Color " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 7. Create a channel for the colored output and send the result
    MapsBridge.CreateChannel("Viridis", (255, 255, 255), True, outputTileSet.Guid)
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Viridis", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()`
    },
    {
      id: 'false-color-multi-channel',
      name: 'False Color - Multi-Channel',
      description: 'Creates separate R, G, B grayscale channels using viridis colormap. Enables independent threshold control, on/off toggle, and additive blending in Maps.',
      category: 'Visualization',
      code: `# MAPS Script Bridge - False Color (Multi-Channel)
# Creates separate grayscale channels (R, G, B) from viridis colormap.
# Output: Three intensity map channels with independent control
# Use when: You want thresholding, segmentation, or independent channel control in Maps

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib.cm as cm

def main():
    # 1. Get the script request from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Get input image filename for channel "0"
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    
    # 3. Load the image and convert to grayscale
    MapsBridge.LogInfo(f"Loading: {input_path}")
    img = Image.open(input_path).convert("L")
    gray_data = np.array(img)
    
    # 4. Apply viridis colormap
    MapsBridge.LogInfo("Applying 'viridis' colormap and separating channels...")
    min_val = gray_data.min()
    max_val = gray_data.max()
    
    if max_val > min_val:
        normalized_data = (gray_data - min_val) / (max_val - min_val)
    else:
        normalized_data = np.zeros_like(gray_data, dtype=float)
    
    # Apply colormap (returns RGBA float array)
    colored_data = cm.viridis(normalized_data)
    
    # 5. Separate into grayscale intensity channels (R, G, B)
    # Each channel is an intensity map (0-255) that Maps will display with the assigned color
    red_channel = (colored_data[:, :, 0] * 255).astype(np.uint8)
    green_channel = (colored_data[:, :, 1] * 255).astype(np.uint8)
    blue_channel = (colored_data[:, :, 2] * 255).astype(np.uint8)
    
    # 6. Save each channel as grayscale PNG
    output_folder = os.path.join(tempfile.gettempdir(), "false_color_multichannel")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    
    red_path = os.path.join(output_folder, f"{base}_red.png")
    green_path = os.path.join(output_folder, f"{base}_green.png")
    blue_path = os.path.join(output_folder, f"{base}_blue.png")
    
    Image.fromarray(red_channel, mode="L").save(red_path)
    Image.fromarray(green_channel, mode="L").save(green_path)
    Image.fromarray(blue_channel, mode="L").save(blue_path)
    
    MapsBridge.LogInfo("Saved R, G, B channels as grayscale intensity maps")
    
    # 7. Create output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Viridis Multi-Channel " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 8. Create three channels with additive blending
    # Each channel gets its corresponding display color
    MapsBridge.CreateChannel("Red Component", (255, 0, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Green Component", (0, 255, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Blue Component", (0, 0, 255), True, outputTileSet.Guid)
    
    # 9. Send each grayscale channel to Maps
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Red Component", red_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Green Component", green_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Blue Component", blue_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(
        f"Tile [{tileInfo.Column}, {tileInfo.Row}] - Viridis colormap as multi-channel.\\n"
        "Toggle R/G/B channels independently, adjust thresholds, or segment by intensity!\\n",
        outputTileSet.Guid
    )
    
    MapsBridge.LogInfo("Done! Three channels created with additive blending.")
    MapsBridge.LogInfo("In Maps: Toggle channels on/off, adjust thresholds independently!")

if __name__ == "__main__":
    main()`
    }
  ];
  
  const editorRef = useRef(null);
  const monacoEditorRef = useRef(null);
  const isEditorChangingRef = useRef(false); // Flag to prevent feedback loop
  const lastEditorChangeTime = useRef(0); // Track when editor was last modified by user
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const textareaRef = useRef(null);

  // Initialize user_id from localStorage or generate new one
  // Load theme from localStorage
  useEffect(() => {
    // Load theme from localStorage
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme) {
      setTheme(storedTheme);
      document.body.className = storedTheme === 'dark' ? 'dark-theme' : '';
    }
  }, []);
  
  // Save theme to localStorage and apply to body when it changes
  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.body.className = theme === 'dark' ? 'dark-theme' : '';
  }, [theme]);

  // Fetch backend version on mount (with cache busting)
  useEffect(() => {
    fetch('/version?t=' + Date.now())
      .then(r => r.json())
      .then(data => setBackendVersion(data.version))
      .catch(() => setBackendVersion('unknown'));
  }, []);

  // Note: AI model is NOT persisted to localStorage - always defaults to flash-lite

  const handleModelChange = (value) => {
    setAiModel(value);
  };

  // Load library scripts on mount
  useEffect(() => {
    loadLibraryScripts();
  }, []);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const scrollToBottom = () => {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
      }
      // Also use the messagesEndRef if available
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    };
    
    // Scroll immediately
    scrollToBottom();
    
    // Also scroll after a short delay to catch any DOM updates
    const timeoutId = setTimeout(scrollToBottom, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '52px';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = Math.min(scrollHeight, 200) + 'px';
    }
  }, [messageInput]);

  // Handle resizing the AI Assistant panel
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizing) {
        const workspace = document.querySelector('.workspace');
        if (workspace) {
          const rect = workspace.getBoundingClientRect();
          const newWidth = rect.right - e.clientX;
          // Constrain between 250px and 70% of workspace width
          const minWidth = 250;
          const maxWidth = rect.width * 0.7;
          setAssistantWidth(Math.max(minWidth, Math.min(maxWidth, newWidth)));
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  // Handle resizing the console output panel
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizingConsole) {
        const outputMainArea = document.querySelector('.output-main-area');
        if (outputMainArea) {
          const rect = outputMainArea.getBoundingClientRect();
          const newHeight = rect.bottom - e.clientY;
          // Constrain between 100px and 80% of viewport height
          const minHeight = 100;
          const maxHeight = consoleExpanded ? window.innerHeight * 0.8 : 400;
          const constrainedHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));
          setConsoleHeight(constrainedHeight);
          // Auto-expand if dragged beyond collapsed max
          if (!consoleExpanded && constrainedHeight > 200) {
            setConsoleExpanded(true);
          }
          // Auto-collapse if dragged below expanded min
          if (consoleExpanded && constrainedHeight < 150) {
            setConsoleExpanded(false);
          }
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizingConsole(false);
    };

    if (isResizingConsole) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizingConsole, consoleExpanded]);

  // Copy console output to clipboard
  const handleCopyConsole = async () => {
    try {
      await navigator.clipboard.writeText(output);
      setToast({ message: 'Console output copied to clipboard', type: 'success' });
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      setToast({ message: 'Failed to copy console output', type: 'error' });
      setTimeout(() => setToast(null), 3000);
    }
  };

  useEffect(() => {
    // Initialize Monaco Editor when editorRef is available and code tab is active
    if (editorRef.current && !monacoEditorRef.current && activeTab === 'code') {
      console.log('[MapsScriptHelper] Initializing Monaco editor (key:', editorKey, ')');
      console.log('[MapsScriptHelper] Initial code length:', code.length);
      console.log('[MapsScriptHelper] Initial code preview:', code.substring(0, 50) + '...');
      monacoEditorRef.current = monaco.editor.create(editorRef.current, {
        value: code,
        language: 'python',
        theme: theme === 'dark' ? 'vs-dark' : 'vs-light',
        automaticLayout: true,
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
      });
      
      monacoEditorRef.current.onDidChangeModelContent(() => {
        isEditorChangingRef.current = true;
        lastEditorChangeTime.current = Date.now();
        const newValue = monacoEditorRef.current.getValue();
        setCode(newValue);
        // Reset flag after a delay to allow fast typing
        setTimeout(() => {
          isEditorChangingRef.current = false;
        }, 100);
      });
      
      console.log('[MapsScriptHelper] Monaco editor initialized successfully');
    }
  }, [activeTab, code, editorKey]);
  
  // Cleanup on unmount only
  useEffect(() => {
    return () => {
      if (monacoEditorRef.current) {
        console.log('[MapsScriptHelper] Disposing Monaco editor');
        monacoEditorRef.current.dispose();
        monacoEditorRef.current = null;
      }
    };
  }, []);
  
  // Update Monaco editor theme when theme changes
  useEffect(() => {
    if (monacoEditorRef.current) {
      monaco.editor.setTheme(theme === 'dark' ? 'vs-dark' : 'vs-light');
    }
  }, [theme]);
  
  // Sync Monaco editor value with code state when code changes externally
  useEffect(() => {
    // Skip syncing if the change came from the editor itself
    if (isEditorChangingRef.current) {
      return;
    }
    
    // Also skip if a user edit happened very recently (within 200ms)
    // This catches fast typing scenarios where React batches updates
    const timeSinceLastEdit = Date.now() - lastEditorChangeTime.current;
    if (timeSinceLastEdit < 200) {
      return;
    }
    
    if (monacoEditorRef.current) {
      const editorValue = monacoEditorRef.current.getValue();
      if (editorValue !== code) {
        console.log('[MapsScriptHelper] Syncing Monaco editor with code state (external change)');
        console.log('[MapsScriptHelper] Current editor value length:', editorValue.length);
        console.log('[MapsScriptHelper] New code value length:', code.length);
        // Store cursor position
        const position = monacoEditorRef.current.getPosition();
        monacoEditorRef.current.setValue(code);
        // Restore cursor position if it's still valid
        if (position) {
          monacoEditorRef.current.setPosition(position);
        }
        console.log('[MapsScriptHelper] Monaco editor synced successfully');
      }
    } else {
      console.log('[MapsScriptHelper] Monaco editor not initialized, code state updated but not synced');
    }
  }, [code]);

  useEffect(() => {
    // Update layout when Python tab becomes active and sync code
    if (activeTab === 'code') {
      if (monacoEditorRef.current) {
        console.log('[MapsScriptHelper] Code tab activated, updating layout');
        setTimeout(() => {
          if (monacoEditorRef.current) {
            monacoEditorRef.current.layout();
            // Sync code when tab becomes active (only if different)
            const editorValue = monacoEditorRef.current.getValue();
            const currentCode = code; // Capture current code value
            if (editorValue !== currentCode) {
              console.log('[MapsScriptHelper] Syncing code on tab activation');
              monacoEditorRef.current.setValue(currentCode);
            }
          }
        }, 100);
      } else {
        console.log('[MapsScriptHelper] Code tab activated but Monaco not initialized yet');
      }
    }
  }, [activeTab]); // Only re-run when tab changes, not when code changes

  // Load library images when Image Finder tab is opened or when opening selection modal
  useEffect(() => {
    if (currentUser && (activeTab === 'image-finder' || showLibrarySelectionModal)) {
      loadLibraryImages();
    }
  }, [activeTab, showLibrarySelectionModal, currentUser]);

  const loadLibraryImages = async () => {
    if (!currentUser) return;
    try {
      const response = await fetch(`/library/images?user_id=${currentUser.id}`);
      const data = await response.json();
      setLibraryImages(data.images || []);
    } catch (error) {
      console.error('[MapsScriptHelper] Failed to load library images:', error);
    }
  };

  const handleLibraryImageSelect = (image) => {
    console.log('[MapsScriptHelper] Image selected from library:', image);
    setSelectedLibraryImage(image);
    // Also clear uploaded file when selecting library image
    setUploadedFile(null);
    
    // If no code loaded, automatically load starter code and switch to code tab
    if (!code || code.trim().length === 0) {
      const starter = `# Start Scripting\n#\n# Tip: scripts should use MapsBridge to read inputs and send outputs.\n# Choose ONE request type:\n#   request = MapsBridge.ScriptTileSetRequest.FromStdIn()\n#   request = MapsBridge.ScriptImageLayerRequest.FromStdIn()\n\nimport MapsBridge\n\n\ndef main():\n    MapsBridge.LogInfo("Ready to script. Add your MAPS Script Bridge logic here.")\n\n\nif __name__ == "__main__":\n    main()\n`;
      setCurrentScript(null);
      setCode(starter);
      if (monacoEditorRef.current) {
        monacoEditorRef.current.setValue(starter);
      }
    }
    
    // Switch to code tab
    setActiveTab('code');
  };

  const handleLibraryImageDelete = async (imageId) => {
    if (!currentUser) return;
    try {
      const response = await fetch(`/library/images/${imageId}?user_id=${currentUser.id}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        // Remove from local state
        setLibraryImages(prev => prev.filter(img => img.id !== imageId));
        // Clear selection if deleted image was selected
        if (selectedLibraryImage && selectedLibraryImage.id === imageId) {
          setSelectedLibraryImage(null);
        }
      } else {
        alert('Failed to delete image');
      }
    } catch (error) {
      alert('Failed to delete image: ' + error.message);
    }
  };

  const handleLibraryUpload = (newImage) => {
    // Add to library images list
    const updatedImages = [...libraryImages, newImage].sort((a, b) => 
      a.name.localeCompare(b.name)
    );
    setLibraryImages(updatedImages);
  };

  const handleLibraryImageSelectFromModal = (image) => {
    console.log('[MapsScriptHelper] Image selected from modal:', image);
    setSelectedLibraryImage(image);
    setUploadedFile(null);
    
    // If no code loaded, automatically load starter code and switch to code tab
    if (!code || code.trim().length === 0) {
      const starter = `# Start Scripting\n#\n# Tip: scripts should use MapsBridge to read inputs and send outputs.\n# Choose ONE request type:\n#   request = MapsBridge.ScriptTileSetRequest.FromStdIn()\n#   request = MapsBridge.ScriptImageLayerRequest.FromStdIn()\n\nimport MapsBridge\n\n\ndef main():\n    MapsBridge.LogInfo("Ready to script. Add your MAPS Script Bridge logic here.")\n\n\nif __name__ == "__main__":\n    main()\n`;
      setCurrentScript(null);
      setCode(starter);
      if (monacoEditorRef.current) {
        monacoEditorRef.current.setValue(starter);
      }
    }
    
    // Switch to code tab
    setActiveTab('code');
  };

  // Load user scripts on mount and when My Scripts tab is opened
  useEffect(() => {
    if (currentUser && activeTab === 'scripts') {
      loadUserScripts();
    }
  }, [activeTab, currentUser]);

  const loadUserScripts = async () => {
    if (!currentUser) return;
    console.log('[MapsScriptHelper] Loading user scripts for user:', currentUser.id);
    try {
      const response = await fetch(`/api/user-scripts?user_id=${currentUser.id}`);
      const data = await response.json();
      console.log('[MapsScriptHelper] Loaded user scripts:', data.scripts?.length || 0, 'scripts');
      setUserScripts(data.scripts || []);
    } catch (error) {
      console.error('[MapsScriptHelper] Failed to load user scripts:', error);
    }
  };
  
  // Load library scripts from database
  const loadLibraryScripts = async () => {
    console.log('[MapsScriptHelper] Loading library scripts from database...');
    try {
      const response = await fetch('/api/library-scripts');
      const data = await response.json();
      console.log('[MapsScriptHelper] Loaded library scripts:', data.scripts?.length || 0, 'scripts');
      setLibraryScripts(data.scripts || []);
    } catch (error) {
      console.error('[MapsScriptHelper] Failed to load library scripts:', error);
      // Fallback to empty array on error
      setLibraryScripts([]);
    }
  };

  const handleSaveScript = async () => {
    if (!scriptName.trim()) {
      alert('Please enter a script name');
      return;
    }

    const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;

    try {
      // If in "Save As" mode, always create a new script (POST)
      // Otherwise, use PUT for existing user-created scripts, POST for new scripts and templates
      const isUpdatingExisting = !isSaveAsMode && currentScript && currentScript.is_user_created;
      const url = isUpdatingExisting ? `/api/user-scripts/${currentScript.id}` : '/api/user-scripts';
      const method = isUpdatingExisting ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: scriptName,
          description: scriptDescription,
          code: currentCode,
          user_id: currentUser.id
        })
      });

      const data = await response.json();
      if (data.success) {
        // Determine success message before closing dialog (which resets flags)
        const message = isSaveAsMode ? 'New version saved successfully!' : 
                       isUpdatingExisting ? 'Script updated successfully!' : 
                       'Script saved successfully!';
        
        // Close dialog and reset flags
        closeSaveDialog();
        
        // Update currentScript with the new/updated data
        setCurrentScript(data.script);
        // Reload user scripts
        loadUserScripts();
        showToast(message, 'success');
      } else {
        showToast('Failed to save script: ' + (data.error || 'Unknown error'), 'error');
      }
    } catch (error) {
      showToast('Failed to save script: ' + error.message, 'error');
    }
  };

  const handleSaveButtonClick = () => {
    setIsSaveAsMode(false); // Reset "Save As" mode
    if (currentScript && currentScript.is_user_created) {
      // Update existing script directly
      const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;
      updateScriptDirectly(currentScript.id, currentCode);
    } else {
      // Show dialog for new script or saving template as new
      // Pre-fill if loading from a template
      if (currentScript && !currentScript.is_user_created) {
        setScriptName(currentScript.name + ' (Copy)');
        setScriptDescription(currentScript.description || '');
      }
      setShowSaveDialog(true);
    }
  };

  const handleSaveAsClick = () => {
    // Always show save dialog to create a new version
    // Pre-fill with current script name + version suffix
    if (currentScript) {
      setScriptName(currentScript.name + ' v2');
      setScriptDescription(currentScript.description || '');
    }
    setIsSaveAsMode(true); // Mark as "Save As" to force creating new script
    setShowSaveDialog(true);
  };

  const closeSaveDialog = () => {
    setShowSaveDialog(false);
    setIsSaveAsMode(false); // Reset "Save As" mode
    setScriptName('');
    setScriptDescription('');
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleClearLogs = async () => {
    if (!confirm('Clear Logs & Analysis?\n\nThis will permanently delete all saved execution logs (successes, failures, sessions, and analysis).')) {
      return;
    }

    try {
      const response = await fetch('/api/logs/clear', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        const d = data.deleted || {};
        showToast(`Logs cleared (failures: ${d.failures || 0}, successes: ${d.successes || 0}, sessions: ${d.sessions || 0}, analysis: ${d.analysis || 0}).`, 'success');
      } else {
        showToast('Failed to clear logs: ' + (data.error || 'Unknown error'), 'error');
      }
    } catch (error) {
      showToast('Failed to clear logs: ' + error.message, 'error');
    }
  };

  const handleDeployScript = async () => {
    if (!currentScript) {
      showToast('No script loaded to deploy', 'error');
      return;
    }

    const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;

    try {
      const response = await fetch('/api/deploy-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_name: currentScript.name,
          code: currentCode
        })
      });

      const data = await response.json();
      if (data.success) {
        showToast(`"${currentScript.name}" deployed to ${data.path}`, 'success');
      } else {
        showToast('Failed to deploy: ' + (data.error || 'Unknown error'), 'error');
      }
    } catch (error) {
      showToast('Failed to deploy: ' + error.message, 'error');
    }
  };

  const updateScriptDirectly = async (scriptId, code) => {
    try {
      const response = await fetch(`/api/user-scripts/${scriptId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: currentScript.name,
          description: currentScript.description,
          code: code,
          user_id: currentUser.id
        })
      });

      const data = await response.json();
      if (data.success) {
        setCurrentScript(data.script);
        loadUserScripts();
        // Show toast notification
        showToast(`"${currentScript.name}" updated successfully!`, 'success');
      } else {
        showToast('Failed to update script: ' + (data.error || 'Unknown error'), 'error');
      }
    } catch (error) {
      showToast('Failed to update script: ' + error.message, 'error');
    }
  };

  const handleLoadScript = (script) => {
    console.log('[MapsScriptHelper] Loading script:', script.name);
    console.log('[MapsScriptHelper] Script code length:', script.code?.length || 0);
    console.log('[MapsScriptHelper] Monaco editor initialized:', !!monacoEditorRef.current);
    
    if (monacoEditorRef.current) {
      console.log('[MapsScriptHelper] Setting code via Monaco editor');
      monacoEditorRef.current.setValue(script.code);
    } else {
      console.log('[MapsScriptHelper] Setting code via state (Monaco not initialized yet)');
      setCode(script.code);
    }
    // Set current script so we can update it directly
    setCurrentScript(script);
    setActiveTab('code');
    console.log('[MapsScriptHelper] Switched to code tab');
  };

  const handleDeleteUserScript = async (scriptId) => {
    if (!confirm('Are you sure you want to delete this script?')) {
      return;
    }

    try {
      const response = await fetch(`/api/user-scripts/${scriptId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Reload user scripts
        loadUserScripts();
      } else {
        alert('Failed to delete script');
      }
    } catch (error) {
      alert('Failed to delete script: ' + error.message);
    }
  };

  const handleCopyToClipboard = async () => {
    try {
      const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;
      await navigator.clipboard.writeText(currentCode);
      showToast('Code copied to clipboard!', 'success');
    } catch (error) {
      showToast('Failed to copy code: ' + error.message, 'error');
    }
  };

  const handleRun = async (overrideImage = null) => {
    // Filter out event objects passed by onClick handlers
    // Only accept override if it's actually an image object with an 'id' property
    const validOverride = overrideImage && typeof overrideImage === 'object' && 'id' in overrideImage ? overrideImage : null;
    
    setIsRunning(true);
    setOutput('Running...');
    setActiveTab('output');
    setOutputFiles([]);
    setOriginalImage(null);
    setResultImage(null);
    setSelectedImage(null);
    setAllFiles([]);
    
    const fd = new FormData();
    const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;
    console.log('[MapsScriptHelper] Preparing to run code');
    console.log('[MapsScriptHelper] Monaco editor ref exists:', !!monacoEditorRef.current);
    console.log('[MapsScriptHelper] Code length:', currentCode?.length || 0);
    console.log('[MapsScriptHelper] First 100 chars:', currentCode?.substring(0, 100));
    
    if (!currentCode || currentCode.trim().length === 0) {
      alert('No code to run! Please load a script or write some code first.');
      setIsRunning(false);
      return;
    }
    
    fd.append('code', currentCode);
    
    // Add user_id from current user
    if (currentUser) {
      fd.append('user_id', currentUser.id);
    }
    
    // Priority: override image > library image > uploaded file
    const imageToUse = validOverride || selectedLibraryImage;
    console.log('[MapsScriptHelper] ===== DETAILED RUN DEBUG =====');
    console.log('[MapsScriptHelper] validOverride:', validOverride);
    console.log('[MapsScriptHelper] selectedLibraryImage:', selectedLibraryImage);
    console.log('[MapsScriptHelper] imageToUse:', imageToUse);
    console.log('[MapsScriptHelper] hasUrl?', imageToUse && imageToUse.url);
    console.log('[MapsScriptHelper] uploadedFile:', uploadedFile);
    console.log('[MapsScriptHelper] ===========================');
    if (imageToUse && imageToUse.url) {
      try {
        // Fetch library image and add to form
        // Use ?raw=true to get the actual TIFF file without PNG conversion
        const imageResponse = await fetch(imageToUse.url + '?raw=true');
        if (!imageResponse.ok) {
          throw new Error(`Failed to fetch image: ${imageResponse.status} ${imageResponse.statusText}`);
        }
        const imageBlob = await imageResponse.blob();
        // Extract the actual filename from the URL (with extension)
        // URL format: /library/images/uuid.tif
        const urlParts = imageToUse.url.split('/');
        const filename = urlParts[urlParts.length - 1];
        const imageFile = new File([imageBlob], filename, { type: imageBlob.type });
        fd.append('image', imageFile);
        fd.append('use_sample', 'false');
      } catch (imageError) {
        const fetchError = `❌ Image Fetch Failed\n\nFailed to load the selected image.\n\nError: ${imageError.message}\n\nImage URL: ${imageToUse.url}`;
        setOutput(fetchError);
        setIsRunning(false);
        alert('Failed to load the selected image. Please try again or select a different image.');
        return;
      }
    } else if (uploadedFile) {
      fd.append('image', uploadedFile);
      fd.append('use_sample', 'false');
    } else {
      // No image selected - show clear error message
      const noImageError = '❌ No Image Selected\n\nPlease select an image from the Image Library tab or upload a new image before running your script.\n\nTo select an image:\n1. Go to the "Image Library" tab\n2. Click on an image to select it\n3. Then click "Run" again';
      setOutput(noImageError);
      setIsRunning(false);
      
      // Show alert for immediate feedback
      alert('Please select an image first!\n\nGo to the "Image Library" tab and select an image, or upload a new one.');
      
      // Switch to Image Library tab to help user
      setActiveTab('image-finder');
      
      return;
    }
    
    try {
      console.log('[MapsScriptHelper] Sending request to /run endpoint');
      console.log('[MapsScriptHelper] FormData entries:');
      for (let pair of fd.entries()) {
        if (pair[0] === 'code') {
          console.log(`  ${pair[0]}: ${pair[1].substring(0, 100)}... (${pair[1].length} chars)`);
        } else if (pair[0] === 'image') {
          console.log(`  ${pair[0]}: ${pair[1].name} (${pair[1].size} bytes)`);
        } else {
          console.log(`  ${pair[0]}: ${pair[1]}`);
        }
      }
      
      const r = await fetch('/run', { method: 'POST', body: fd });
      
      // Check if response is JSON
      const contentType = r.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await r.json();
      } else {
        // If not JSON, read as text
        const text = await r.text();
        const serverError = `❌ Server Error\n\nStatus: ${r.status} ${r.statusText}\n\nResponse:\n${text.substring(0, 1000)}`;
        setOutput(serverError);
        const errorData = {
          error: `Server Error: ${r.status} ${r.statusText}`,
          message: serverError,
          code: currentCode
        };
        setLastError(errorData);
        // Increment consecutive failures counter
        const newFailureCount = consecutiveFailures + 1;
        setConsecutiveFailures(newFailureCount);
        // Prompt user to send error details to AI chat
        sendErrorToAI(errorData, newFailureCount);
        setIsRunning(false);
        return;
      }
      
      if (!r.ok) {
        // Format detailed error information for debugging
        let errorMessage = '';
        
        // Special handling for timeout
        if (r.status === 504 || data.error === 'Execution timed out') {
          errorMessage = '⏱️ Execution Timed Out\n\n';
          errorMessage += data.message || 'Script execution exceeded the timeout limit.\n\n';
          if (data.timeout) {
            errorMessage += `Timeout: ${data.timeout} seconds\n`;
          }
          errorMessage += '\nTip: Consider optimizing your code or breaking it into smaller steps.';
        } else {
          errorMessage = '❌ Execution Failed\n\n';
          
          // Add diagnostic mode activation message if present
          if (data.diagnostic_mode && data.diagnostic_mode.activated) {
            errorMessage += '🔍 ' + data.diagnostic_mode.message + '\n\n';
          }
          
          if (data.error) {
            errorMessage += `Error: ${data.error}\n\n`;
          }
          
          if (data.message) {
            errorMessage += `${data.message}\n\n`;
          }
          
          if (data.return_code !== undefined) {
            errorMessage += `Exit Code: ${data.return_code}\n\n`;
          }
          
          if (data.stderr && data.stderr !== '(no error output)') {
            errorMessage += `━━━ STDERR ━━━\n${data.stderr}\n\n`;
          }
          
          if (data.stdout && data.stdout !== '(no output)') {
            errorMessage += `━━━ STDOUT ━━━\n${data.stdout}`;
          }
          
          // If no specific error info, show the full response
          if (!data.error && !data.stderr && !data.stdout && !data.message) {
            errorMessage += JSON.stringify(data, null, 2);
          }
        }
        
        setOutput(errorMessage);
        // Store error for AI context
        const errorData = {
          error: data.error || 'Execution failed',
          stderr: data.stderr,
          stdout: data.stdout,
          return_code: data.return_code,
          message: errorMessage,
          code: currentCode
        };
        setLastError(errorData);
        
        // Increment consecutive failures counter
        const newFailureCount = consecutiveFailures + 1;
        setConsecutiveFailures(newFailureCount);
        
        // Prompt user to send error details to AI chat
        sendErrorToAI(errorData, newFailureCount);
        
        setIsRunning(false);
        return;
      }
      
      // Build success message with diagnostic mode notifications
      let successMessage = '✅ Success\n\n';
      
      // Add diagnostic mode notifications
      if (data.diagnostic_mode) {
        if (data.diagnostic_mode.activated) {
          successMessage += '🔍 ' + data.diagnostic_mode.message + '\n\n';
        }
        if (data.diagnostic_mode.deactivated) {
          successMessage += '✓ ' + data.diagnostic_mode.message + '\n\n';
          // Update code editor with cleaned code
          if (data.diagnostic_mode.cleaned_code && monacoEditorRef.current) {
            monacoEditorRef.current.setValue(data.diagnostic_mode.cleaned_code);
            setCode(data.diagnostic_mode.cleaned_code);
            animateCodeUpdate();
          }
        }
      }
      
      successMessage += '━━━ STDOUT ━━━\n' + (data.stdout || '(no output)');
      setOutput(successMessage);
      
      // Clear error on success
      setLastError(null);
      setConsecutiveFailures(0); // Reset failure counter on success
      
      // Store user_id if returned from backend
      if (data.user_id && data.user_id !== userId) {
        setUserId(data.user_id);
        localStorage.setItem('userId', data.user_id);
      }
      
      // Build complete file list including original image
      const files = [];
      if (data.original_url) {
        const originalUrl = data.original_url + '?t=' + Date.now();
        setOriginalImage(originalUrl);
        // Extract file extension from URL to determine correct type
        const urlWithoutParams = data.original_url.split('?')[0];
        const fileExtension = urlWithoutParams.match(/\.(png|jpg|jpeg|gif|bmp|svg|tiff|tif)$/i);
        const fileType = fileExtension ? fileExtension[0].toLowerCase() : '.png';
        files.push({
          name: 'Original Image',
          url: originalUrl,
          type: fileType,
          isOriginal: true
        });
      }
      
      if (data.output_files) {
        setOutputFiles(data.output_files);
        files.push(...data.output_files.map(f => ({
          ...f,
          url: f.url + '?t=' + Date.now()
        })));
      }
      
      setAllFiles(files);
      
      // Auto-select original image if available, otherwise select first image
      const imageFiles = files.filter(f => ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type));
      const originalImageFile = imageFiles.find(f => f.isOriginal);
      const imageToSelect = originalImageFile || imageFiles[0];
      if (imageToSelect) {
        setSelectedImage(imageToSelect.url);
      }
      setIsRunning(false);
    } catch (e) {
      const requestError = `❌ Request Failed\n\nError: ${e.message}\n\n${e.stack ? `Stack trace:\n${e.stack}` : ''}`;
      setOutput(requestError);
      const errorData = {
        error: `Request Failed: ${e.message}`,
        message: requestError,
        code: monacoEditorRef.current ? monacoEditorRef.current.getValue() : code
      };
      setLastError(errorData);
      // Increment consecutive failures counter
      const newFailureCount = consecutiveFailures + 1;
      setConsecutiveFailures(newFailureCount);
      // Prompt user to send error details to AI chat
      sendErrorToAI(errorData, newFailureCount);
      setIsRunning(false);
    }
  };

  // Function to animate code update in editor
  const animateCodeUpdate = () => {
    setIsCodeUpdating(true);
    // Add flash animation class to editor container
    // Find the editor container parent element
    const editorContainer = editorRef.current?.parentElement;
    if (editorContainer) {
      editorContainer.classList.add('code-update-flash');
      setTimeout(() => {
        if (editorContainer) {
          editorContainer.classList.remove('code-update-flash');
        }
        setIsCodeUpdating(false);
      }, 1500);
    } else {
      setIsCodeUpdating(false);
    }
    
    // Also highlight all lines briefly using Monaco decorations
    if (monacoEditorRef.current && typeof monaco !== 'undefined') {
      try {
        const model = monacoEditorRef.current.getModel();
        if (model) {
          const lineCount = model.getLineCount();
          const decorations = [];
          
          // Create decorations for all lines
          for (let i = 1; i <= lineCount; i++) {
            decorations.push({
              range: new monaco.Range(i, 1, i, model.getLineMaxColumn(i)),
              options: {
                className: 'code-update-highlight',
                isWholeLine: true,
                stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
              }
            });
          }
          
          const decorationIds = monacoEditorRef.current.deltaDecorations([], decorations);
          
          // Remove decorations after animation
          setTimeout(() => {
            if (monacoEditorRef.current) {
              monacoEditorRef.current.deltaDecorations(decorationIds, []);
            }
          }, 1500);
        }
      } catch (error) {
        console.warn('[MapsScriptHelper] Failed to add Monaco decorations:', error);
      }
    }
  };

  // Format message text with markdown-like formatting
  const formatMessage = (text) => {
    if (!text) return '';
    
    let formatted = text;
    
    // Escape HTML first to prevent XSS
    formatted = formatted
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    // Format code blocks (```code```)
    formatted = formatted.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre><code class="code-block">${code.trim()}</code></pre>`;
    });
    
    // Format inline code (`code`)
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Format bold (**text** or __text__)
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__(.+?)__/g, '<strong>$1</strong>');
    
    // Format italic (*text* or _text_)
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/_(.+?)_/g, '<em>$1</em>');
    
    // Format numbered lists (1. item)
    formatted = formatted.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="list-item numbered">$1. $2</div>');
    
    // Format bullet lists (- item or * item)
    formatted = formatted.replace(/^[-*]\s+(.+)$/gm, '<div class="list-item">• $1</div>');
    
    // Format line breaks (preserve double line breaks as paragraphs)
    formatted = formatted.split('\n\n').map(para => {
      if (para.trim().startsWith('<')) return para; // Don't wrap HTML elements
      return `<p>${para.replace(/\n/g, '<br>')}</p>`;
    }).join('');
    
    // Format checkmarks and emojis
    formatted = formatted.replace(/✅/g, '<span class="emoji">✅</span>');
    
    return formatted;
  };

  // Function to prompt user before sending error details to the AI chat
  const sendErrorToAI = (errorData, failureCount = 1) => {
    // Check if debug logging is already present in the code
    const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;
    const hasDebugLogging = currentCode.includes('[AUTO-DEBUG]') || currentCode.includes('AUTO-DEBUG MODE ACTIVE');
    
    // After 2+ failures, offer verbose debugging (but only if not already present)
    if (failureCount >= 2 && !hasDebugLogging) {
      const promptText = "The script failed again. Can I add debugging statements to help me diagnose it? Once I figure out the problem, they will be removed.";
      
      // Avoid spamming duplicate prompts
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (
          last &&
          last.type === 'assistant' &&
          last.text.includes('debugging statements') &&
          last.quickReplies &&
          Array.isArray(last.quickReplies) &&
          last.quickReplies.some(q => q && q._kind === 'debug_inject_prompt')
        ) {
          return prev;
        }

        return [
          ...prev,
          {
            type: 'assistant',
            text: promptText,
            quickReplies: [
              {
                _kind: 'debug_inject_prompt',
                icon: 'bug_report',
                text: 'Yes, add debugging',
                sendText: 'Yes — add debugging statements to help diagnose the issue.',
                description: 'Inject verbose logging to identify the problem'
              },
              {
                _kind: 'debug_inject_prompt',
                icon: 'close',
                text: 'No, I\'ll fix it',
                action: 'dismiss',
                description: 'Dismiss and fix manually'
              }
            ]
          }
        ];
      });
    } else if (hasDebugLogging && failureCount >= 2) {
      // Debug logging already present - ask AI to analyze and fix
      const promptText = "The script is still failing with verbose debugging enabled. Can I analyze the debug output and fix the issue?";
      
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (
          last &&
          last.type === 'assistant' &&
          last.text.includes('verbose debugging enabled') &&
          last.quickReplies &&
          Array.isArray(last.quickReplies) &&
          last.quickReplies.some(q => q && q._kind === 'fix_with_debug_prompt')
        ) {
          return prev;
        }

        return [
          ...prev,
          {
            type: 'assistant',
            text: promptText,
            quickReplies: [
              {
                _kind: 'fix_with_debug_prompt',
                icon: 'auto_fix_high',
                text: 'Yes, analyze and fix',
                sendText: 'Yes — analyze the debug output and fix the issue.',
                description: 'Use verbose output to diagnose and fix the problem'
              },
              {
                _kind: 'fix_with_debug_prompt',
                icon: 'close',
                text: 'No, I\'ll fix it',
                action: 'dismiss',
                description: 'Dismiss and fix manually'
              }
            ]
          }
        ];
      });
    } else {
      // First failure: Standard error help prompt
      const promptText = "My code failed with an error. Can you help me fix it?";

      // Avoid spamming duplicate prompts
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (
          last &&
          last.type === 'assistant' &&
          last.text === promptText &&
          last.quickReplies &&
          Array.isArray(last.quickReplies) &&
          last.quickReplies.some(q => q && q._kind === 'error_help_prompt')
        ) {
          return prev;
        }

        return [
          ...prev,
          {
            type: 'assistant',
            text: promptText,
            quickReplies: [
              {
                _kind: 'error_help_prompt',
                icon: 'check',
                text: 'Yes',
                sendText: 'Yes — help me fix it.',
                description: 'Send error details (stderr/stdout) + current code to the AI'
              },
              {
                _kind: 'error_help_prompt',
                icon: 'close',
                text: 'No',
                action: 'dismiss',
                description: 'Dismiss this prompt'
              }
            ]
          }
        ];
      });
    }
  };

  const handleSendMessage = async (overrideText = null) => {
    // Ensure message is always a string, never an object
    let userMessage = '';
    if (overrideText !== null && overrideText !== undefined) {
      // Convert to string and handle objects gracefully
      if (typeof overrideText === 'object') {
        console.error('Received object instead of string:', overrideText);
        userMessage = JSON.stringify(overrideText);
      } else {
        userMessage = String(overrideText);
      }
    } else {
      userMessage = String(messageInput);
    }

    if (userMessage.trim()) {
      const newMessages = [...messages, { type: 'user', text: userMessage }];
      setMessages(newMessages);
      setMessageInput('');
      
      // Add loading message with special loading flag
      const loadingMessages = [...newMessages, { type: 'assistant', text: '', isLoading: true }];
      setMessages(loadingMessages);
      
      try {
        // Get current code as context
        const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;
        
        // Get selected image URL if available
        const imageUrl = selectedImage || null;
        
        // Build context including error information if available
        let contextParts = [];
        if (currentCode) {
          contextParts.push(`Current code:\n${currentCode.substring(0, 8000)}`);
        }
        if (lastError) {
          contextParts.push(`\n\nLast execution error:\n${lastError.message}`);
          if (lastError.stderr && lastError.stderr !== '(no error output)') {
            contextParts.push(`\nSTDERR:\n${lastError.stderr}`);
          }
          if (lastError.stdout && lastError.stdout !== '(no output)') {
            contextParts.push(`\nSTDOUT:\n${lastError.stdout}`);
          }
        }
        
        // Call backend AI API
        let response;
        let data;
        try {
        response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              messages: newMessages.map(m => ({ 
                role: m.type === 'user' ? 'user' : 'assistant', 
                content: typeof m.text === 'string' ? m.text : String(m.text || '')
              })),
              context: contextParts.length > 0 ? contextParts.join('\n') : null,
              image_url: imageUrl,
              model: aiModel
            })
          });
          
          // Check if response is OK
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error (${response.status}): ${errorText.substring(0, 200)}`);
          }
          
          // Try to parse JSON
          try {
            data = await response.json();
          } catch (jsonError) {
            throw new Error(`Invalid response format: ${await response.text()}`);
          }
        } catch (fetchError) {
          // Network or parsing error
          throw new Error(`Failed to communicate with AI service: ${fetchError.message}`);
        }
        
        if (data.success) {
          // Create assistant message - use response if available, otherwise empty string
          const assistantMessage = { type: 'assistant', text: data.response || '', quickReplies: data.quick_replies || null };
          
          console.log('[MapsScriptHelper] AI Response received:');
          console.log('[MapsScriptHelper]   - Response text length:', (data.response || '').length);
          console.log('[MapsScriptHelper]   - Has suggested_code:', !!data.suggested_code);
          if (data.suggested_code) {
            console.log('[MapsScriptHelper]   - Code length:', data.suggested_code.length);
          }
          
          // If AI suggests code updates, apply them to the editor (even if response is empty)
          if (data.suggested_code && data.suggested_code.trim()) {
            const codeToSet = data.suggested_code.trim();
            let updateSuccess = false;
            
            // Get current code to compare
            let currentCode = '';
            if (monacoEditorRef.current) {
              currentCode = monacoEditorRef.current.getValue().trim();
            } else {
              currentCode = code.trim();
            }
            
            // Only update if the code is actually different
            const codeChanged = currentCode !== codeToSet;
            
            if (monacoEditorRef.current) {
              try {
                console.log('[MapsScriptHelper] [CODE UPDATE] Attempting to update Monaco editor...');
                console.log('[MapsScriptHelper] [CODE UPDATE] Current code length:', currentCode.length);
                console.log('[MapsScriptHelper] [CODE UPDATE] New code length:', codeToSet.length);
                console.log('[MapsScriptHelper] [CODE UPDATE] Code changed?', codeChanged);
                
                // Force Monaco to update with executeEdits for better reliability
                const model = monacoEditorRef.current.getModel();
                if (model) {
                  const fullRange = model.getFullModelRange();
                  monacoEditorRef.current.executeEdits('ai-update', [{
                    range: fullRange,
                    text: codeToSet,
                    forceMoveMarkers: true
                  }]);
                  console.log('[MapsScriptHelper] [CODE UPDATE] Used executeEdits method');
                } else {
                  // Fallback to setValue
                  monacoEditorRef.current.setValue(codeToSet);
                  console.log('[MapsScriptHelper] [CODE UPDATE] Used setValue method (model not available)');
                }
                
                // Small delay to let Monaco process the update
                await new Promise(resolve => setTimeout(resolve, 50));
                
                // Verify the update worked by reading it back
                const verifyCode = monacoEditorRef.current.getValue();
                console.log('[MapsScriptHelper] [CODE UPDATE] Verified code length:', verifyCode.length);
                console.log('[MapsScriptHelper] [CODE UPDATE] Match?', verifyCode === codeToSet);
                
                if (verifyCode === codeToSet || verifyCode.trim() === codeToSet.trim()) {
                  // Also update the code state
                  setCode(codeToSet);
                  updateSuccess = true;
                  if (codeChanged) {
                    // Only add message if it's not already in the response
                    if (!assistantMessage.text.includes('✅ Code has been updated')) {
                      assistantMessage.text += '\n\n✅ Code has been updated in the editor!';
                    }
                    console.log('[MapsScriptHelper] ✓ [SUCCESS] Code updated and verified in editor');
                    // Animate the code update
                    animateCodeUpdate();
                  }
                } else {
                  console.error('[MapsScriptHelper] [CODE UPDATE] Verification failed!');
                  console.error('[MapsScriptHelper] [CODE UPDATE] Expected first 100 chars:', codeToSet.substring(0, 100));
                  console.error('[MapsScriptHelper] [CODE UPDATE] Got first 100 chars:', verifyCode.substring(0, 100));
                  // Try one more time with setValue
                  monacoEditorRef.current.setValue(codeToSet);
                  await new Promise(resolve => setTimeout(resolve, 50));
                  const verifyCode2 = monacoEditorRef.current.getValue();
                  if (verifyCode2 === codeToSet || verifyCode2.trim() === codeToSet.trim()) {
                    setCode(codeToSet);
                    updateSuccess = true;
                    if (codeChanged) {
                      if (!assistantMessage.text.includes('✅ Code has been updated')) {
                        assistantMessage.text += '\n\n✅ Code has been updated (retry succeeded)!';
                      }
                      animateCodeUpdate();
                    }
                  } else {
                    // Still update state as fallback
                    setCode(codeToSet);
                    updateSuccess = false;
                    if (!assistantMessage.text.includes('Code has been updated')) {
                      assistantMessage.text += '\n\n⚠️ Code update may have failed. Please check the editor.';
                    }
                  }
                }
              } catch (error) {
                console.error('[MapsScriptHelper] [CODE UPDATE] Exception:', error);
                // Fallback: update state anyway
                setCode(codeToSet);
                updateSuccess = false;
                if (!assistantMessage.text.includes('Code has been updated')) {
                  assistantMessage.text += '\n\n⚠️ Code update error. Please copy the code manually.';
                }
              }
            } else {
              // Editor not ready, update state anyway
              console.warn('[MapsScriptHelper] [CODE UPDATE] Monaco editor not available, updating state only');
              setCode(codeToSet);
              updateSuccess = true;
              if (codeChanged) {
                // Only add message if it's not already in the response
                if (!assistantMessage.text.includes('✅ Code has been updated')) {
                  assistantMessage.text += '\n\n✅ Code state updated (editor will sync)!';
                }
                console.log('[MapsScriptHelper] ✓ Code updated in state (editor not ready):', codeToSet.substring(0, 100) + '...');
              }
            }
            
            if (!updateSuccess) {
              assistantMessage.text += '\n\n⚠️ Code update failed. Please copy the code manually from the message above.';
            }

            // If we're on the Welcome screen, jump to the editor to show the generated code
            if (activeTab === 'welcome') {
              setCurrentScript(null);
              setActiveTab('code');
              setEditorKey(prev => prev + 1);
            }
          } else if (data.suggested_code === '') {
            console.warn('[MapsScriptHelper] ⚠️ Empty suggested_code received (empty string)');
          } else {
            console.log('[MapsScriptHelper] ℹ️ No code update - AI response was text-only');
          }
          
          // Only add message if there's content (response text or code update message)
          if (assistantMessage.text.trim()) {
            setMessages([...newMessages, assistantMessage]);
          }
        } else {
          // Build detailed error message - always show all available details
          let errorMessage = '❌ AI Request Failed\n\n';
          
          // Always show the main error message
          if (data.error) {
            errorMessage += `**Error:** ${data.error}`;
          } else if (data.full_error) {
            errorMessage += `**Error:** ${data.full_error}`;
          } else {
            errorMessage += 'Sorry, I encountered an error. Please try again.';
          }
          
          // Show error type
          if (data.error_type) {
            errorMessage += `\n\n**Error Type:** ${data.error_type}`;
          }
          
          // Show full error if available
          if (data.full_error && data.full_error !== data.error) {
            errorMessage += `\n\n**Full Error:** ${data.full_error}`;
          }
          
          // Show prompt feedback
          if (data.prompt_feedback) {
            errorMessage += `\n\n**Prompt Feedback:** ${data.prompt_feedback}`;
          }
          
          // Show API response
          if (data.api_response) {
            errorMessage += `\n\n**API Response:** ${data.api_response}`;
          }
          
          // Show error arguments if available
          if (data.error_args) {
            errorMessage += `\n\n**Error Arguments:** ${data.error_args}`;
          }
          
          // Show simplified traceback (always included)
          if (data.error_traceback) {
            errorMessage += `\n\n**Error Details:**\n\`\`\`\n${data.error_traceback}\n\`\`\``;
          }
          
          // Show full traceback if in debug mode
          if (data.traceback) {
            errorMessage += `\n\n**Full Traceback:**\n\`\`\`\n${data.traceback}\n\`\`\``;
          }
          
          // Log full error object to console for debugging
          console.error('[MapsScriptHelper] AI Chat Error - Full Details:', JSON.stringify(data, null, 2));
          console.error('[MapsScriptHelper] AI Chat Error - Error Object:', data);
          
          setMessages([...newMessages, { 
            type: 'assistant', 
            text: errorMessage
          }]);
        }
      } catch (error) {
        // Network or parsing errors
        let errorMessage = '❌ Connection Error\n\n';
        errorMessage += `Failed to communicate with AI service.\n\n**Error:** ${error.message}`;
        
        if (error.name) {
          errorMessage += `\n\n**Error Type:** ${error.name}`;
        }
        
        console.error('[MapsScriptHelper] AI Chat Network Error:', error);
        setMessages([...newMessages, { 
          type: 'assistant', 
          text: errorMessage
        }]);
      }
      
      // Auto-scroll is handled by useEffect hook
    }
  };

  const files = [
    { name: 'main.py', type: 'file' },
    { name: 'utils.py', type: 'file' },
    { name: 'requirements.txt', type: 'file' },
    { name: 'data', type: 'folder' }
  ];

  // Show login screen if no user is logged in
  if (!currentUser) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="app-container">
      {/* Tab Bar */}
      <div className="tab-bar">
        <div className="tab-logo">
          <span className="material-symbols-outlined">map</span>
          <span className="logo-text">Maps</span>
        </div>
        <button 
          className={`tab-button ${activeTab === 'code' ? 'active' : ''}`}
          onClick={() => setActiveTab('code')}
        >
          Python
        </button>
        <button 
          className={`tab-button ${activeTab === 'output' ? 'active' : ''}`}
          onClick={() => setActiveTab('output')}
        >
          Output
        </button>
        <button 
          className={`tab-button ${activeTab === 'image-finder' ? 'active' : ''}`}
          onClick={() => setActiveTab('image-finder')}
        >
          Image Library
        </button>
        <button 
          className={`tab-button ${activeTab === 'scripts' ? 'active' : ''}`}
          onClick={() => setActiveTab('scripts')}
        >
          Scripts
        </button>
        <button 
          className={`tab-button ${activeTab === 'help' ? 'active' : ''}`}
          onClick={() => setActiveTab('help')}
        >
          Help
        </button>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            className={`tab-button ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0 12px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#666' }}>
              account_circle
            </span>
            <span style={{ fontSize: '14px', color: '#666', fontWeight: '500' }}>
              {currentUser?.name || 'User'}
            </span>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: '6px 12px',
              background: 'transparent',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#666',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#f5f5f5';
              e.currentTarget.style.borderColor = '#999';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.borderColor = '#ddd';
            }}
            title="Log out"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
              logout
            </span>
            Logout
          </button>
          {backendVersion && (
            <div className="tab-version">
              <span className="version-text">v{backendVersion}</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Workspace */}
      <div className="workspace">
        <div className="main-content" style={{ 
          width: (activeTab === 'image-finder' || activeTab === 'scripts' || activeTab === 'settings' || activeTab === 'help') 
            ? '100%' 
            : `calc(100% - ${assistantWidth}px - 4px)` 
        }}>
          <div className="content-panel">
            {/* Welcome Screen - Shown on login */}
            {activeTab === 'welcome' && (
              <div className="code-layout" style={{
                display: 'grid',
                height: '100%',
                gridTemplateColumns: isPanelCollapsed ? '60px 1fr' : '280px 1fr'
              }}>
                {/* Left Panel */}
                <div className={`file-panel ${isPanelCollapsed ? 'collapsed' : ''}`}>
                  <button 
                    className="panel-collapse-btn" 
                    onClick={() => setIsPanelCollapsed(!isPanelCollapsed)}
                    title={isPanelCollapsed ? "Expand panel" : "Collapse panel"}
                  >
                    <span className="material-symbols-outlined">
                      {isPanelCollapsed ? 'chevron_right' : 'chevron_left'}
                    </span>
                  </button>
                  
                  <div className={`file-toolbar ${!currentScript ? 'no-script' : ''}`}>
                    <button className="md-button md-button-filled" onClick={handleRun} title="Run script">
                      <span className="material-symbols-outlined" style={{fontSize: '18px'}}>play_arrow</span>
                      {!isPanelCollapsed && 'Run'}
                    </button>
                    <button className="md-button md-button-outlined" onClick={handleSaveButtonClick} title={currentScript && currentScript.is_user_created ? `Update "${currentScript.name}"` : "Save script to My Scripts"}>
                      <span className="material-symbols-outlined" style={{fontSize: '18px'}}>save</span>
                      {!isPanelCollapsed && (currentScript && currentScript.is_user_created ? 'Update' : 'Save Script')}
                    </button>
                    {currentScript && currentScript.is_user_created && (
                      <button className="md-button md-button-outlined" onClick={handleSaveAsClick} title="Save as new version with different name">
                        <span className="material-symbols-outlined" style={{fontSize: '18px'}}>save_as</span>
                        {!isPanelCollapsed && 'Save As'}
                      </button>
                    )}
                    <button 
                      className="md-button md-button-outlined" 
                      onClick={handleDeployScript} 
                      disabled={!currentScript}
                      title="Load a script first"
                    >
                      <span className="material-symbols-outlined" style={{fontSize: '18px'}}>upload</span>
                      {!isPanelCollapsed && 'Deploy Script'}
                    </button>
                    <button 
                      className="md-button md-button-outlined" 
                      onClick={() => {
                        if (monacoEditorRef.current) {
                          monacoEditorRef.current.setValue('');
                        }
                        setCode('');
                      }}
                      title="Copy code to clipboard"
                    >
                      <span className="material-symbols-outlined" style={{fontSize: '18px'}}>content_copy</span>
                      {!isPanelCollapsed && 'Copy Code'}
                    </button>
                  </div>

                  {!isPanelCollapsed && (
                    <div className="image-selection-buttons">
                      <button 
                        className="md-button md-button-outlined" 
                        style={{marginTop: '16px'}}
                        onClick={() => setShowLibrarySelectionModal(true)}
                        title="Select an image from your library"
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '18px'}}>photo_library</span>
                        Select from Library
                      </button>
                      
                      <button 
                        className="md-button md-button-outlined" 
                        style={{marginTop: '8px'}}
                        onClick={() => document.getElementById('file-input').click()}
                        title="Upload a new image file"
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '18px'}}>upload_file</span>
                        Upload New Image
                      </button>
                    </div>
                  )}
                </div>
                
                {/* Selected Image Thumbnail - Also show on welcome screen */}
                {!isPanelCollapsed && (selectedLibraryImage || uploadedFile) && (
                  <div className="selected-image-thumbnail">
                    <div className="thumbnail-header">
                      <span style={{fontSize: '12px', fontWeight: '500', color: '#666'}}>Selected Image</span>
                      <button
                        className="thumbnail-clear"
                        onClick={() => {
                          setSelectedLibraryImage(null);
                          setUploadedFile(null);
                        }}
                        title="Clear selection"
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '16px'}}>close</span>
                      </button>
                    </div>
                    <div className="thumbnail-preview">
                      {selectedLibraryImage ? (
                        <>
                          <img src={selectedLibraryImage.url} alt={selectedLibraryImage.name} className="thumbnail-preview-image" />
                          <button
                            className="thumbnail-preview-view-btn"
                            onClick={() => {
                              setViewerImage(selectedLibraryImage);
                              setShowImageViewer(true);
                            }}
                            title="View image in full size"
                          >
                            <span className="material-symbols-outlined">zoom_in</span>
                          </button>
                          <div className="thumbnail-info">
                            <div className="thumbnail-name">{selectedLibraryImage.name}</div>
                            <div className="thumbnail-type" style={{
                              backgroundColor: selectedLibraryImage.type === 'SEM' ? '#1976d2' : selectedLibraryImage.type === 'SDB' ? '#388e3c' : '#f57c00'
                            }}>
                              {selectedLibraryImage.type}
                            </div>
                          </div>
                        </>
                      ) : (
                        <>
                          <img src={URL.createObjectURL(uploadedFile)} alt={uploadedFile.name} className="thumbnail-preview-image" />
                          <button
                            className="thumbnail-preview-view-btn"
                            onClick={() => {
                              setViewerImage({
                                url: URL.createObjectURL(uploadedFile),
                                name: uploadedFile.name
                              });
                              setShowImageViewer(true);
                            }}
                            title="View image in full size"
                          >
                            <span className="material-symbols-outlined">zoom_in</span>
                          </button>
                          <div className="thumbnail-info">
                            <div className="thumbnail-name">{uploadedFile.name}</div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Welcome Content */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  background: isDark
                    ? 'linear-gradient(135deg, #0f1115 0%, #151a22 100%)'
                    : 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)',
                  padding: '40px',
                  overflow: 'auto'
                }}>
                  <div style={{
                    maxWidth: '800px',
                    width: '100%',
                    textAlign: 'center'
                  }}>
                    <div style={{
                      margin: '0 auto 24px'
                    }}>
                      <MapsAILogo size={160} showText={true} />
                    </div>
                    
                    <h1 style={{
                      fontSize: '36px',
                      fontWeight: '400',
                      margin: '0 0 12px 0',
                      color: isDark ? '#f3f4f6' : '#1c1b1f'
                    }}>Welcome to MAPS Script Helper</h1>
                    <p style={{
                      fontSize: '16px',
                      color: isDark ? '#b6bcc8' : '#49454f',
                      margin: '0 0 40px 0'
                    }}>
                      Develop and test Python scripts for MAPS Script Bridge with instant feedback
                    </p>
                    
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '20px',
                      marginBottom: '32px'
                    }}>
                      <div className="md3-card md3-card-filled welcome-card-small" onClick={() => {
                        const starter = `# Start Scripting\n#\n# Tip: scripts should use MapsBridge to read inputs and send outputs.\n# Choose ONE request type:\n#   request = MapsBridge.ScriptTileSetRequest.FromStdIn()\n#   request = MapsBridge.ScriptImageLayerRequest.FromStdIn()\n\nimport MapsBridge\n\n\ndef main():\n    MapsBridge.LogInfo("Ready to script. Add your MAPS Script Bridge logic here.")\n\n\nif __name__ == \"__main__\":\n    main()\n`;
                        setCurrentScript(null);
                        setCode(starter);
                        setActiveTab('code');
                      }} style={{cursor: 'pointer'}}>
                        <div className="md3-card-content">
                          <div className="md3-card-icon">
                            <span className="material-symbols-outlined">code</span>
                          </div>
                          <h3 className="md3-title-large">Start Scripting</h3>
                          <p className="md3-body-medium">Open the editor with a blank starter script (no template required)</p>
                        </div>
                        <div className="md3-card-state-layer"></div>
                      </div>

                      <div className="md3-card md3-card-filled welcome-card-small" onClick={() => setActiveTab('scripts')} style={{cursor: 'pointer'}}>
                        <div className="md3-card-content">
                          <div className="md3-card-icon">
                            <span className="material-symbols-outlined">inventory_2</span>
                          </div>
                          <h3 className="md3-title-large">Browse Example Scripts</h3>
                          <p className="md3-body-medium">Start with ready-to-use templates for common EM image processing tasks</p>
                        </div>
                        <div className="md3-card-state-layer"></div>
                      </div>

                      <div className="md3-card md3-card-filled welcome-card-small" onClick={() => setActiveTab('image-finder')} style={{cursor: 'pointer'}}>
                        <div className="md3-card-content">
                          <div className="md3-card-icon">
                            <span className="material-symbols-outlined">photo_library</span>
                          </div>
                          <h3 className="md3-title-large">Browse Image Library</h3>
                          <p className="md3-body-medium">View and select images from your library to use with scripts</p>
                        </div>
                        <div className="md3-card-state-layer"></div>
                      </div>

                      <div className="md3-card md3-card-filled welcome-card-small" onClick={async () => {
                        // Quick Start: Load image, script, and run
                        try {
                          // 1. Load library images if not already loaded
                          let imagesToSearch = libraryImages;
                          if (imagesToSearch.length === 0 && currentUser) {
                            const response = await fetch(`/library/images?user_id=${currentUser.id}`);
                            const data = await response.json();
                            imagesToSearch = data.images || [];
                            setLibraryImages(imagesToSearch);
                          }
                          
                          // 2. Find the specific image
                          const targetImageName = 'Tile_004-003-000000_2-000.s0001_e00';
                          const imageToLoad = imagesToSearch.find(img => 
                            img.name.includes(targetImageName) || img.name === targetImageName
                          ) || (imagesToSearch.length > 0 ? imagesToSearch[0] : null);
                          
                          if (!imageToLoad) {
                            alert(`Image "${targetImageName}" not found in library. Please upload it first.`);
                            setActiveTab('image-finder');
                            return;
                          }
                          
                          // 3. Set the image first
                          setSelectedLibraryImage(imageToLoad);
                          
                          // 4. Find and load the False Color - Single Image script
                          // Try to find in library scripts, fallback to legacy
                          const scriptToLoad = exampleScripts.find(s => s.id === 'false-color-single-image') || 
                                              legacyExampleScripts.find(s => s.id === 'false-color-single-image');
                          if (!scriptToLoad) {
                            alert('False Color - Single Image script not found.');
                            return;
                          }
                          
                          // 5. Load the script (this switches to code tab)
                          handleLoadScript(scriptToLoad);
                          
                          // 6. Wait for script to load, then run with the image directly
                          // Pass imageToLoad directly to handleRun to avoid state update timing issues
                          setTimeout(async () => {
                            await handleRun(imageToLoad);
                          }, 500);
                        } catch (error) {
                          console.error('Quick Start error:', error);
                          alert('Quick Start failed: ' + error.message);
                        }
                      }} style={{cursor: 'pointer'}}>
                        <div className="md3-card-content">
                          <div className="md3-card-icon" style={{background: '#4caf50'}}>
                            <span className="material-symbols-outlined">rocket_launch</span>
                          </div>
                          <h3 className="md3-title-large">Quick Start</h3>
                          <p className="md3-body-medium">Load sample image and False Color script, then run automatically</p>
                        </div>
                        <div className="md3-card-state-layer"></div>
                      </div>
                    </div>

                    <div style={{ marginTop: '24px', textAlign: 'center' }}>
                      <div style={{ marginBottom: '12px', color: isDark ? '#b6bcc8' : '#49454f', fontSize: '14px', fontWeight: '500' }}>
                        Try a starter AI prompt:
                      </div>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
                        <button
                          className="md-button md-button-outlined"
                          onClick={() => handleSendMessage("Tell me about MapsBridge.py: what it does, the core API vs helper functions, and show a minimal example script using the helpers.")}
                          title="Send this prompt to the AI assistant"
                        >
                          Tell me about MapsBridge.py
                        </button>
                        <button
                          className="md-button md-button-outlined"
                          onClick={() => handleSendMessage("Create a script that applies false color mapping to a grayscale EM image using a colormap like viridis or plasma.")}
                          title="Send this prompt to the AI assistant"
                        >
                          Create a false color visualization
                        </button>
                        <button
                          className="md-button md-button-outlined"
                          onClick={() => handleSendMessage("Create a script that detects and counts particles in an EM image and displays the count.")}
                          title="Send this prompt to the AI assistant"
                        >
                          Detect and count particles
                        </button>
                        <button
                          className="md-button md-button-outlined"
                          onClick={() => handleSendMessage("Create a script that detects edges and outputs them.")}
                          title="Send this prompt to the AI assistant"
                        >
                          Create an edge detection script
                        </button>
                        <button
                          className="md-button md-button-outlined"
                          onClick={() => handleSendMessage("Create a script that enhances image contrast using histogram equalization.")}
                          title="Send this prompt to the AI assistant"
                        >
                          Apply contrast enhancement
                        </button>
                        <button
                          className="md-button md-button-outlined"
                          onClick={() => handleSendMessage("Help me understand this error and how to fix it. [Paste your error message here]")}
                          title="Send this prompt to the AI assistant"
                        >
                          Help me debug my script
                        </button>
                      </div>
                    </div>

                    <div style={{ marginTop: '24px', textAlign: 'center' }}>
                      <button
                        className="md-button md-button-outlined"
                        onClick={() => setActiveTab('help')}
                        title="View help documentation"
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: '16px', verticalAlign: 'middle', marginRight: '4px' }}>help</span>
                        Help & Documentation
                      </button>
                    </div>

                    <div style={{
                      marginTop: '32px',
                      padding: '16px 20px',
                      background: isDark ? 'rgba(25, 118, 210, 0.12)' : '#E8F4FD',
                      borderRadius: '12px',
                      borderLeft: isDark ? '4px solid rgba(25, 118, 210, 0.8)' : '4px solid #1976D2',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      textAlign: 'left'
                    }}>
                      <span className="material-symbols-outlined" style={{color: isDark ? '#90caf9' : '#1976D2', fontSize: '24px'}}>
                        info
                      </span>
                      <span style={{color: isDark ? '#cfe8ff' : '#0D47A1', fontSize: '14px'}}>
                        Scripts written here work in both the helper app and real MAPS
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Code Tab - Always rendered but hidden when not active */}
            <div className="code-layout" style={{
              display: activeTab === 'code' ? 'grid' : 'none', 
              height: '100%',
              gridTemplateColumns: isPanelCollapsed ? '60px 1fr' : '280px 1fr'
            }}>
              <div className={`file-panel ${isPanelCollapsed ? 'collapsed' : ''}`}>
                {/* Collapse/Expand Button */}
                <button 
                  className="panel-collapse-btn" 
                  onClick={() => setIsPanelCollapsed(!isPanelCollapsed)}
                  title={isPanelCollapsed ? "Expand panel" : "Collapse panel"}
                >
                  <span className="material-symbols-outlined">
                    {isPanelCollapsed ? 'chevron_right' : 'chevron_left'}
                  </span>
                </button>
                
                {/* Current Script Name Display - Moved above toolbar */}
                {currentScript && (
                  <div className="current-script-display">
                    <span className="material-symbols-outlined" style={{fontSize: '16px', color: '#6750A4'}}>
                      {currentScript.is_user_created ? 'edit_note' : 'inventory_2'}
                    </span>
                    <span className="current-script-name">{currentScript.name}</span>
                    {currentScript.is_user_created && (
                      <span className="current-script-badge">My Script</span>
                    )}
                    <button
                      className="clear-script-btn"
                      onClick={() => {
                        setCurrentScript(null);
                        if (monacoEditorRef.current) {
                          monacoEditorRef.current.setValue('');
                        }
                        setCode('');
                      }}
                      title="Clear and start new script"
                    >
                      <span className="material-symbols-outlined" style={{fontSize: '16px'}}>close</span>
                    </button>
                  </div>
                )}
                
                <div className={`file-toolbar ${!currentScript ? 'no-script' : ''}`}>
                  <button className="md-button md-button-filled" onClick={handleRun} title="Run script">
                    <span className="material-symbols-outlined" style={{fontSize: '18px'}}>play_arrow</span>
                    {!isPanelCollapsed && 'Run'}
                  </button>
                  <button className="md-button md-button-outlined" onClick={handleSaveButtonClick} title={currentScript && currentScript.is_user_created ? `Update "${currentScript.name}"` : "Save script to My Scripts"}>
                    <span className="material-symbols-outlined" style={{fontSize: '18px'}}>save</span>
                    {!isPanelCollapsed && (currentScript && currentScript.is_user_created ? 'Update' : 'Save Script')}
                  </button>
                  {currentScript && currentScript.is_user_created && (
                    <button className="md-button md-button-outlined" onClick={handleSaveAsClick} title="Save as new version with different name">
                      <span className="material-symbols-outlined" style={{fontSize: '18px'}}>save_as</span>
                      {!isPanelCollapsed && 'Save As'}
                    </button>
                  )}
                  <button 
                    className="md-button md-button-outlined" 
                    onClick={handleDeployScript} 
                    disabled={!currentScript}
                    title={currentScript ? `Deploy "${currentScript.name}" to C:\\project\\Python` : "Load a script first"}
                  >
                    <span className="material-symbols-outlined" style={{fontSize: '18px'}}>upload</span>
                    {!isPanelCollapsed && 'Deploy Script'}
                  </button>
                  <button className="md-button md-button-outlined" onClick={handleCopyToClipboard} title="Copy code to clipboard">
                    <span className="material-symbols-outlined" style={{fontSize: '18px'}}>content_copy</span>
                    {!isPanelCollapsed && 'Copy Code'}
                  </button>
                </div>
                
                {/* Image Selection Buttons */}
                <div className="image-selection-buttons" style={{padding: isPanelCollapsed ? '8px' : '12px', borderTop: '1px solid #e0e0e0'}}>
                  {isPanelCollapsed ? (
                    <>
                      <button 
                        className="md-button md-button-outlined" 
                        onClick={() => setShowLibrarySelectionModal(true)}
                        title="Select from Library"
                        style={{width: '44px', height: '44px', minWidth: '44px', padding: 0, justifyContent: 'center', borderRadius: '50%', marginBottom: '8px'}}
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '18px'}}>image</span>
                      </button>
                      <button 
                        className="md-button md-button-outlined" 
                        onClick={() => setShowUploadModal(true)}
                        title="Upload New Image"
                        style={{width: '44px', height: '44px', minWidth: '44px', padding: 0, justifyContent: 'center', borderRadius: '50%'}}
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '18px'}}>upload</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button 
                        className="md-button md-button-outlined" 
                        onClick={() => setShowLibrarySelectionModal(true)}
                        style={{width: '100%', marginBottom: '8px', fontSize: '12px', padding: '8px 12px'}}
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '16px'}}>image</span>
                        Select from Library
                      </button>
                      <button 
                        className="md-button md-button-outlined" 
                        onClick={() => setShowUploadModal(true)}
                        style={{width: '100%', fontSize: '12px', padding: '8px 12px'}}
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '16px'}}>upload</span>
                        Upload New Image
                      </button>
                    </>
                  )}
                </div>
                
                {/* Selected Image Thumbnail - Moved to bottom */}
                {(selectedLibraryImage || uploadedFile) && (
                  <div className="selected-image-thumbnail">
                    <div className="thumbnail-header">
                      <span style={{fontSize: '12px', fontWeight: '500', color: '#666'}}>Selected Image</span>
                      <button
                        className="thumbnail-clear"
                        onClick={() => {
                          setSelectedLibraryImage(null);
                          setUploadedFile(null);
                        }}
                        title="Clear selection"
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '16px'}}>close</span>
                      </button>
                    </div>
                    <div className="thumbnail-preview">
                      {selectedLibraryImage ? (
                        <>
                          <img src={selectedLibraryImage.url} alt={selectedLibraryImage.name} className="thumbnail-preview-image" />
                          <button
                            className="thumbnail-preview-view-btn"
                            onClick={() => {
                              setViewerImage(selectedLibraryImage);
                              setShowImageViewer(true);
                            }}
                            title="View image in full size"
                          >
                            <span className="material-symbols-outlined">zoom_in</span>
                          </button>
                          <div className="thumbnail-info">
                            <div className="thumbnail-name">{selectedLibraryImage.name}</div>
                            <div className="thumbnail-type" style={{
                              backgroundColor: selectedLibraryImage.type === 'SEM' ? '#1976d2' : selectedLibraryImage.type === 'SDB' ? '#388e3c' : '#f57c00'
                            }}>
                              {selectedLibraryImage.type}
                            </div>
                          </div>
                        </>
                      ) : (
                        <>
                          <img src={URL.createObjectURL(uploadedFile)} alt={uploadedFile.name} className="thumbnail-preview-image" />
                          <button
                            className="thumbnail-preview-view-btn"
                            onClick={() => {
                              setViewerImage({
                                url: URL.createObjectURL(uploadedFile),
                                name: uploadedFile.name
                              });
                              setShowImageViewer(true);
                            }}
                            title="View image in full size"
                          >
                            <span className="material-symbols-outlined">zoom_in</span>
                          </button>
                          <div className="thumbnail-info">
                            <div className="thumbnail-name">{uploadedFile.name}</div>
                            <div className="thumbnail-type" style={{backgroundColor: '#666'}}>Uploaded</div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
              <div className="editor-container">
                <div id="monaco-editor" ref={editorRef}></div>
                {/* Welcome Screen overlay removed - only show main welcome screen on welcome tab */}
                {false && !code && (
                  <div className="md3-welcome-overlay">
                    <div className="md3-welcome-container">
                      <div className="md3-welcome-header">
                        <div className="md3-welcome-icon-large">
                          <MapsAILogo size={180} showText={true} />
                        </div>
                        <h1 className="md3-display-small">Welcome to MAPS Script Helper</h1>
                        <p className="md3-body-large md3-welcome-subtitle">
                          Develop and test Python scripts for MAPS Script Bridge with instant feedback
                        </p>
                      </div>
                      
                      <div className="md3-welcome-cards">
                        <div className="md3-card md3-card-filled" onClick={() => {
                          // Create a minimal starter script so the editor opens without selecting a template
                          const starter = `# Start Scripting\n#\n# Tip: scripts should use MapsBridge to read inputs and send outputs.\n# Choose ONE request type:\n#   request = MapsBridge.ScriptTileSetRequest.FromStdIn()\n#   request = MapsBridge.ScriptImageLayerRequest.FromStdIn()\n\nimport MapsBridge\n\n\ndef main():\n    MapsBridge.LogInfo(\"Ready to script. Add your MAPS Script Bridge logic here.\")\n\n\nif __name__ == \"__main__\":\n    main()\n`;

                          setCurrentScript(null);
                          if (monacoEditorRef.current) {
                            monacoEditorRef.current.setValue(starter);
                          }
                          setCode(starter);
                          setActiveTab('code');
                        }}>
                          <div className="md3-card-content">
                            <div className="md3-card-icon">
                              <span className="material-symbols-outlined">code</span>
                            </div>
                            <h3 className="md3-title-large">Start Scripting</h3>
                            <p className="md3-body-medium">Open the editor with a blank starter script (no template required)</p>
                          </div>
                          <div className="md3-card-state-layer"></div>
                        </div>

                        <div className="md3-card md3-card-filled" onClick={() => setActiveTab('scripts')}>
                          <div className="md3-card-content">
                            <div className="md3-card-icon">
                              <span className="material-symbols-outlined">inventory_2</span>
                            </div>
                            <h3 className="md3-title-large">Browse Example Scripts</h3>
                            <p className="md3-body-medium">Start with ready-to-use templates for common EM image processing tasks</p>
                          </div>
                          <div className="md3-card-state-layer"></div>
                        </div>
                      </div>

                      {/* Starter AI prompts */}
                      <div style={{ marginTop: '24px', textAlign: 'center' }}>
                        <div className="md3-label-large" style={{ marginBottom: '12px', color: '#3c3c3c' }}>
                          Try a starter AI prompt:
                        </div>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
                          <button
                            className="md-button md-button-outlined"
                            onClick={() => handleSendMessage("Tell me about MapsBridge.py: what it does, the core API vs helper functions, and show a minimal example script using the helpers.")}
                            title="Send this prompt to the AI assistant"
                          >
                            Tell me about MapsBridge.py
                          </button>
                          <button
                            className="md-button md-button-outlined"
                            onClick={() => handleSendMessage("Create a script that applies false color mapping to a grayscale EM image using a colormap like viridis or plasma.")}
                            title="Send this prompt to the AI assistant"
                          >
                            Create a false color visualization
                          </button>
                          <button
                            className="md-button md-button-outlined"
                            onClick={() => handleSendMessage("Create a script that detects and counts particles in an EM image and displays the count.")}
                            title="Send this prompt to the AI assistant"
                          >
                            Detect and count particles
                          </button>
                          <button
                            className="md-button md-button-outlined"
                            onClick={() => handleSendMessage("Create a script that detects edges and outputs them.")}
                            title="Send this prompt to the AI assistant"
                          >
                            Create an edge detection script
                          </button>
                          <button
                            className="md-button md-button-outlined"
                            onClick={() => handleSendMessage("Create a script that enhances image contrast using histogram equalization.")}
                            title="Send this prompt to the AI assistant"
                          >
                            Apply contrast enhancement
                          </button>
                          <button
                            className="md-button md-button-outlined"
                            onClick={() => handleSendMessage("Help me understand this error and how to fix it. [Paste your error message here]")}
                            title="Send this prompt to the AI assistant"
                          >
                            Help me debug my script
                          </button>
                        </div>
                      </div>
                      
                      <div className="md3-welcome-tip">
                        <span className="material-symbols-outlined md3-tip-icon">lightbulb</span>
                        <span className="md3-label-large">Scripts written here work in both the helper app and real MAPS</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Modals for Python Tab */}
            <LibrarySelectionModal
              isOpen={showLibrarySelectionModal}
              onClose={() => setShowLibrarySelectionModal(false)}
              onSelect={handleLibraryImageSelectFromModal}
              libraryImages={libraryImages}
            />
            <UploadModal
              isOpen={showUploadModal && activeTab === 'code'}
              onClose={() => {
                setShowUploadModal(false);
              }}
              currentUser={currentUser}
              onUpload={(newImage) => {
                handleLibraryUpload(newImage);
                // After upload, automatically select the uploaded image
                setSelectedLibraryImage(newImage);
                setUploadedFile(null);
              }}
            />

            {/* Save Script Dialog */}
            {showSaveDialog && (
              <div className="modal-overlay" onClick={closeSaveDialog}>
                <div className="modal-content save-script-dialog" onClick={(e) => e.stopPropagation()}>
                  <div className="modal-header">
                    <h2>{isSaveAsMode ? 'Save As New Version' : 'Save Script'}</h2>
                    <button className="modal-close" onClick={closeSaveDialog}>
                      <span className="material-symbols-outlined">close</span>
                    </button>
                  </div>
                  <div className="modal-body">
                    <div className="form-group">
                      <label className="form-label">Script Name *</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g., My Image Filter"
                        value={scriptName}
                        onChange={(e) => setScriptName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSaveScript()}
                        autoFocus
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Description (optional)</label>
                      <textarea
                        className="form-textarea"
                        placeholder="Describe what this script does..."
                        value={scriptDescription}
                        onChange={(e) => setScriptDescription(e.target.value)}
                        rows="3"
                      />
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button className="md-button" onClick={closeSaveDialog}>
                      Cancel
                    </button>
                    <button className="md-button md-button-filled" onClick={handleSaveScript}>
                      <span className="material-symbols-outlined" style={{fontSize: '18px'}}>save</span>
                      {isSaveAsMode ? 'Save As New' : 'Save'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Output Tab */}
            {activeTab === 'output' && (
              <div className="output-container">
                <div className="output-layout-with-sidebar">
                  {/* Sidebar with thumbnails and files */}
                  <div className="output-sidebar">
                    <div className="output-sidebar-header">
                      <h3>Files & Images</h3>
                    </div>
                    <div className="output-sidebar-content">
                      {allFiles.length === 0 ? (
                        <div className="empty-state">
                          <span className="material-symbols-outlined" style={{fontSize: '48px', color: '#ccc', marginBottom: '8px'}}>image</span>
                          <p style={{color: '#999', fontSize: '14px'}}>No files yet. Run your script to see results.</p>
                        </div>
                      ) : (
                        <>
                          {/* Original Image Section - Always shown if available */}
                          {allFiles.filter(f => f.isOriginal && ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type)).length > 0 && (
                            <div className="sidebar-section">
                              <div className="sidebar-section-header">Original Image</div>
                              <div className="thumbnails-list">
                                {allFiles
                                  .filter(f => f.isOriginal && ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type))
                                  .map((file, idx) => (
                                    <Thumbnail
                                      key={idx}
                                      file={file}
                                      isSelected={selectedImage === file.url}
                                      onClick={setSelectedImage}
                                      onView={(file) => {
                                        setViewerImage(file);
                                        setShowImageViewer(true);
                                      }}
                                    />
                                  ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Separator between original and script outputs */}
                          {allFiles.filter(f => f.isOriginal && ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type)).length > 0 &&
                           allFiles.filter(f => !f.isOriginal && ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type)).length > 0 && (
                            <div className="sidebar-separator">
                              <div className="separator-line"></div>
                              <div className="separator-label">Script Outputs</div>
                              <div className="separator-line"></div>
                            </div>
                          )}
                          
                          {/* Script Output Images */}
                          {allFiles.filter(f => !f.isOriginal && ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type)).length > 0 && (
                            <div className="sidebar-section">
                              <div className="sidebar-section-header">
                                {allFiles.filter(f => f.isOriginal && ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type)).length > 0 
                                  ? 'Script Outputs' 
                                  : 'Images'}
                              </div>
                              <div className="thumbnails-list">
                                {allFiles
                                  .filter(f => !f.isOriginal && ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type))
                                  .map((file, idx) => (
                                    <Thumbnail
                                      key={idx}
                                      file={file}
                                      isSelected={selectedImage === file.url}
                                      onClick={setSelectedImage}
                                      onView={(file) => {
                                        setViewerImage(file);
                                        setShowImageViewer(true);
                                      }}
                                    />
                                  ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Report files */}
                          {allFiles.filter(f => !['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type)).length > 0 && (
                            <div className="sidebar-section">
                              <div className="sidebar-section-header">Reports & Files</div>
                              <div className="files-list">
                                {allFiles
                                  .filter(f => !['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif'].includes(f.type))
                                  .map((file, idx) => (
                                    <FileIcon key={idx} file={file} />
                                  ))}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  
                  {/* Main image viewing area */}
                  <div className="output-main-area">
                    {isRunning ? (
                      <div className="main-image-loading">
                        <div className="loading-spinner"></div>
                        <h3 style={{color: '#1976d2', fontWeight: '500', marginTop: '24px'}}>Processing...</h3>
                        <p style={{color: '#666', fontSize: '14px', marginTop: '8px'}}>Running your Python script</p>
                      </div>
                    ) : selectedImage ? (
                      <ImageViewer 
                        src={selectedImage} 
                        alt="Selected Image" 
                        title={allFiles.find(f => f.url === selectedImage)?.name || 'Image'}
                        isDark={isDark}
                      />
                    ) : (
                      <div className="main-image-placeholder">
                        <span className="material-symbols-outlined" style={{fontSize: '64px', color: '#ccc', marginBottom: '16px'}}>image</span>
                        <h3 style={{color: '#999', fontWeight: '400'}}>Main Image Area</h3>
                        <p style={{color: '#bbb', fontSize: '14px', marginTop: '8px'}}>Click a thumbnail to view an image</p>
                      </div>
                    )}
                    
                    {/* Console Output */}
                    <div 
                      className={`output-console-section ${consoleExpanded ? 'expanded' : ''}`}
                      style={{ 
                        height: `${consoleHeight}px`, 
                        maxHeight: consoleExpanded ? 'none' : '80vh',
                        minHeight: consoleExpanded ? '200px' : '100px'
                      }}
                    >
                      <div 
                        className="console-resize-handle"
                        onMouseDown={(e) => {
                          e.preventDefault();
                          setIsResizingConsole(true);
                        }}
                      />
                      <div className="output-console-header">
                        <h3>Console Output</h3>
                        <div className="output-console-actions">
                          <button 
                            className="console-action-btn"
                            onClick={handleCopyConsole}
                            title="Copy console output"
                          >
                            <span className="material-symbols-outlined">content_copy</span>
                          </button>
                          <button 
                            className="console-action-btn"
                            onClick={() => {
                              setConsoleExpanded(!consoleExpanded);
                              if (!consoleExpanded) {
                                // When expanding, set to a larger default height
                                setConsoleHeight(Math.max(consoleHeight, 400));
                              } else {
                                // When collapsing, set to smaller height
                                setConsoleHeight(Math.min(consoleHeight, 200));
                              }
                            }}
                            title={consoleExpanded ? "Collapse console" : "Expand console"}
                          >
                            <span className="material-symbols-outlined">
                              {consoleExpanded ? 'unfold_less' : 'unfold_more'}
                            </span>
                          </button>
                        </div>
                      </div>
                      <div className="output-content">{output}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Image Library Tab */}
            {activeTab === 'image-finder' && (
              <div 
                className={`image-finder-container ${isDragging ? 'drag-over' : ''}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsDragging(true);
                }}
                onDragLeave={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  // Only set dragging to false if we're leaving the container itself
                  if (e.currentTarget === e.target) {
                    setIsDragging(false);
                  }
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsDragging(false);
                  
                  const files = Array.from(e.dataTransfer.files);
                  // Helper function to check if file is an image
                  const isImageFile = (file) => {
                    if (file.type && file.type.startsWith('image/')) {
                      return true;
                    }
                    const extension = file.name.toLowerCase().match(/\.[^.]+$/);
                    if (extension) {
                      const imageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.tif', '.webp', '.ico'];
                      return imageExtensions.includes(extension[0]);
                    }
                    return false;
                  };
                  const imageFiles = files.filter(file => isImageFile(file));
                  
                  if (imageFiles.length > 0) {
                    // Open upload modal with the first file pre-selected
                    const file = imageFiles[0];
                    setShowUploadModal(true);
                    // Store file temporarily to pre-fill the upload modal
                    setTimeout(() => {
                      const fileInput = document.querySelector('.upload-modal-file-input');
                      if (fileInput && fileInput.files.length === 0) {
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(file);
                        fileInput.files = dataTransfer.files;
                        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                      }
                    }, 100);
                  }
                }}
              >
                <div className="image-finder-header">
                  <h2>Image Library</h2>
                  <button
                    className="md-button md-button-filled"
                    onClick={() => setShowUploadModal(true)}
                  >
                    <span className="material-symbols-outlined" style={{fontSize: '18px'}}>upload</span>
                    Upload Image
                  </button>
                </div>
                
                {isDragging && (
                  <div className="drag-overlay">
                    <div className="drag-overlay-content">
                      <span className="material-symbols-outlined" style={{fontSize: '64px', color: '#1976d2', marginBottom: '16px'}}>cloud_upload</span>
                      <h3 style={{color: '#1976d2', fontWeight: '500', marginBottom: '8px'}}>Drop image here to upload</h3>
                      <p style={{color: '#666', fontSize: '14px'}}>Release to open upload dialog</p>
                    </div>
                  </div>
                )}
                
                {libraryImages.length === 0 ? (
                  <div className="empty-library">
                    <span className="material-symbols-outlined" style={{fontSize: '64px', color: '#ccc', marginBottom: '16px'}}>image</span>
                    <h3 style={{color: '#999', fontWeight: '400', marginBottom: '8px'}}>No images in library</h3>
                    <p style={{color: '#bbb', fontSize: '14px', marginBottom: '24px'}}>Drag and drop an image here or click upload to get started</p>
                    <button
                      className="md-button md-button-filled"
                      onClick={() => setShowUploadModal(true)}
                    >
                      <span className="material-symbols-outlined" style={{fontSize: '18px'}}>upload</span>
                      Upload Image
                    </button>
                  </div>
                ) : (
                  <>
                    {libraryImages.filter(img => img.user_id).length > 0 && (
                      <div className="library-section">
                        <div className="sidebar-separator">
                          <div className="separator-line"></div>
                          <div className="separator-label">Your Images</div>
                          <div className="separator-line"></div>
                        </div>
                        <div className="library-grid">
                          {libraryImages
                            .filter(img => img.user_id)
                            .map((image) => (
                              <LibraryImageCard
                                key={image.id}
                                image={image}
                                isSelected={selectedLibraryImage && selectedLibraryImage.id === image.id}
                                onSelect={handleLibraryImageSelect}
                                onDelete={handleLibraryImageDelete}
                                onView={(img) => {
                                  setViewerImage(img);
                                  setShowImageViewer(true);
                                }}
                              />
                            ))}
                        </div>
                      </div>
                    )}
                    
                    {libraryImages.filter(img => img.user_id).length > 0 && libraryImages.filter(img => !img.user_id).length > 0 && (
                      <div className="sidebar-separator">
                        <div className="separator-line"></div>
                        <div className="separator-label">Library Images</div>
                        <div className="separator-line"></div>
                      </div>
                    )}
                    
                    {libraryImages.filter(img => !img.user_id).length > 0 && (
                      <div className="library-section">
                        {libraryImages.filter(img => img.user_id).length === 0 && (
                          <div className="sidebar-separator">
                            <div className="separator-line"></div>
                            <div className="separator-label">Images</div>
                            <div className="separator-line"></div>
                          </div>
                        )}
                        <div className="library-grid">
                          {libraryImages
                            .filter(img => !img.user_id)
                            .map((image) => (
                              <LibraryImageCard
                                key={image.id}
                                image={image}
                                isSelected={selectedLibraryImage && selectedLibraryImage.id === image.id}
                                onSelect={handleLibraryImageSelect}
                                onDelete={handleLibraryImageDelete}
                                onView={(img) => {
                                  setViewerImage(img);
                                  setShowImageViewer(true);
                                }}
                              />
                            ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
                <UploadModal
                  isOpen={showUploadModal}
                  onClose={() => setShowUploadModal(false)}
                  currentUser={currentUser}
                  onUpload={handleLibraryUpload}
                />
              </div>
            )}

            {/* My Scripts Tab */}
            {activeTab === 'scripts' && (
              <div className="scripts-container">
                {/* Sub-tabs for Scripts - MD3 Style at Top */}
                <div className="scripts-sub-tabs">
                  <button
                    className={`scripts-sub-tab ${scriptsSubTab === 'templates' ? 'active' : ''}`}
                    onClick={() => setScriptsSubTab('templates')}
                  >
                    <span className="material-symbols-outlined">inventory_2</span>
                    Default Templates
                  </button>
                  <button
                    className={`scripts-sub-tab ${scriptsSubTab === 'user' ? 'active' : ''}`}
                    onClick={() => setScriptsSubTab('user')}
                  >
                    <span className="material-symbols-outlined">edit_note</span>
                    My Scripts
                    {userScripts.length > 0 && (
                      <span className="scripts-count-badge">{userScripts.length}</span>
                    )}
                  </button>
                </div>

                {/* Tab Content Container */}
                <div className="scripts-container-inner">
                  {/* Templates Tab Content */}
                  {scriptsSubTab === 'templates' && (
                    <div className="scripts-tab-content">
                    <div className="md-card scripts-header-card">
                      <div className="scripts-header-title">
                        <span className="material-symbols-outlined" style={{color: '#1976d2', fontSize: '28px'}}>inventory_2</span>
                        <div>
                          <h2>Default Templates</h2>
                          <p className="scripts-subtitle">Pre-built examples to get you started</p>
                        </div>
                      </div>
                    </div>
                    <div className="scripts-grid">
                      {exampleScripts.map((script) => (
                        <div 
                          key={script.id} 
                          className="script-card default-template"
                          onClick={() => handleLoadScript(script)}
                        >
                          <div className="script-badge template-badge">Template</div>
                          <div className="script-card-header">
                            <span className="material-symbols-outlined script-icon">code</span>
                            <span className="script-category">{script.category}</span>
                          </div>
                          <h3 className="script-name">{script.name}</h3>
                          <p className="script-description">{script.description}</p>
                          <div className="script-card-footer">
                            <span className="load-script-hint">
                              <span className="material-symbols-outlined">arrow_forward</span>
                              Load Script
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* User Scripts Tab Content */}
                {scriptsSubTab === 'user' && (
                  <div className="scripts-tab-content">
                    <div className="md-card scripts-header-card">
                      <div className="scripts-header-title">
                        <span className="material-symbols-outlined" style={{color: '#388e3c', fontSize: '28px'}}>edit_note</span>
                        <div>
                          <h2>My Scripts</h2>
                          <p className="scripts-subtitle">Your saved scripts</p>
                        </div>
                      </div>
                    </div>
                    {userScripts.length === 0 ? (
                      <div className="empty-scripts">
                        <span className="material-symbols-outlined" style={{fontSize: '64px', color: '#ccc'}}>note_add</span>
                        <p style={{fontSize: '16px', color: '#666', marginTop: '16px'}}>No saved scripts yet</p>
                        <p style={{fontSize: '14px', color: '#999'}}>Click "Save Script" in the Code tab to save your first script!</p>
                      </div>
                    ) : (
                      <div className="scripts-grid">
                        {userScripts.map((script) => (
                          <div 
                            key={script.id} 
                            className="script-card user-script"
                            onClick={() => handleLoadScript(script)}
                          >
                            <div className="script-badge user-badge">My Script</div>
                            <button 
                              className="script-delete-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteUserScript(script.id);
                              }}
                              title="Delete script"
                            >
                              <span className="material-symbols-outlined">delete</span>
                            </button>
                            <div className="script-card-header">
                              <span className="material-symbols-outlined script-icon">code</span>
                              <span className="script-date">{new Date(script.created_at).toLocaleDateString()}</span>
                            </div>
                            <h3 className="script-name">{script.name}</h3>
                            <p className="script-description">{script.description || 'No description'}</p>
                            <div className="script-card-footer">
                              <span className="load-script-hint">
                                <span className="material-symbols-outlined">arrow_forward</span>
                                Load Script
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="settings-container">
                <div className="md-card settings-header-card">
                  <h2>Settings</h2>
                  <p className="settings-subtitle">Configure your helper app preferences</p>
                </div>

                {/* Appearance Section */}
                <div className="settings-section">
                  <div className="md-card">
                    <h3 className="settings-section-title">
                      <span className="material-symbols-outlined" style={{color: '#f57c00', fontSize: '24px'}}>palette</span>
                      Appearance
                    </h3>
                    <p className="settings-section-description">
                      Choose between light and dark theme for the interface.
                    </p>
                    
                    <div className="settings-info-box">
                      <div style={{marginBottom: '16px'}}>
                        <label style={{display: 'block', marginBottom: '12px', fontWeight: '500'}}>
                          <span className="material-symbols-outlined" style={{fontSize: '18px', verticalAlign: 'middle', marginRight: '4px'}}>
                            {theme === 'dark' ? 'dark_mode' : 'light_mode'}
                          </span>
                          Theme
                        </label>
                        <div style={{display: 'flex', gap: '10px'}}>
                          <button
                            onClick={() => setTheme('light')}
                            style={{
                              flex: 1,
                              padding: '12px 20px',
                              background: theme === 'light' ? '#1976d2' : '#f5f5f5',
                              color: theme === 'light' ? 'white' : '#333',
                              border: theme === 'light' ? 'none' : '1px solid #ddd',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '14px',
                              fontWeight: theme === 'light' ? '500' : 'normal',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '8px',
                              transition: 'all 0.2s'
                            }}
                          >
                            <span className="material-symbols-outlined" style={{fontSize: '20px'}}>light_mode</span>
                            Light Mode
                          </button>
                          <button
                            onClick={() => setTheme('dark')}
                            style={{
                              flex: 1,
                              padding: '12px 20px',
                              background: theme === 'dark' ? '#1976d2' : '#f5f5f5',
                              color: theme === 'dark' ? 'white' : '#333',
                              border: theme === 'dark' ? 'none' : '1px solid #ddd',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '14px',
                              fontWeight: theme === 'dark' ? '500' : 'normal',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '8px',
                              transition: 'all 0.2s'
                            }}
                          >
                            <span className="material-symbols-outlined" style={{fontSize: '20px'}}>dark_mode</span>
                            Dark Mode
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Script Deployment Section */}
                <div className="settings-section">
                  <div className="md-card">
                    <h3 className="settings-section-title">
                      <span className="material-symbols-outlined" style={{color: '#6750A4', fontSize: '24px'}}>folder</span>
                      Script Deployment
                    </h3>
                    <p className="settings-section-description">
                      When you click the "Deploy Script" button in the Code tab, your script will be saved as a Python file 
                      to your local filesystem. The file will overwrite any existing file with the same name.
                    </p>
                    
                    <div className="settings-info-box">
                      <div className="settings-info-header">
                        <span className="material-symbols-outlined" style={{color: '#6750A4', fontSize: '20px'}}>folder_open</span>
                        <strong>Deploy Location</strong>
                      </div>
                      <div className="settings-info-path">
                        <code>C:\project\Python\</code>
                      </div>
                      <p className="settings-info-note">
                        <span className="material-symbols-outlined" style={{fontSize: '16px', verticalAlign: 'middle'}}>info</span>
                        This folder is mounted from your host machine into the Docker container
                      </p>
                    </div>

                    <div className="settings-usage">
                      <h4>How to Deploy Scripts</h4>
                      <ol>
                        <li>Load or create a script in the <strong>Code</strong> tab</li>
                        <li>Click the <strong>Deploy Script</strong> button</li>
                        <li>Your script will be saved to <code>C:\project\Python\[script-name].py</code></li>
                        <li>Use the deployed script in your MAPS workflows</li>
                      </ol>
                    </div>
                  </div>
                </div>

                {/* Logs & Analysis Section */}
                <div className="settings-section">
                  <div className="md-card">
                    <h3 className="settings-section-title">
                      <span className="material-symbols-outlined" style={{color: '#6750A4', fontSize: '24px'}}>analytics</span>
                      Logs & Analysis
                    </h3>
                    <p className="settings-section-description">
                      View script execution logs and analysis. Every script execution (success or failure) is automatically logged 
                      to help the AI learn and improve over time.
                    </p>

                    <div style={{display: 'flex', justifyContent: 'flex-end', marginTop: '8px'}}>
                      <button
                        className="md-button md-button-outlined"
                        onClick={handleClearLogs}
                        title="Delete all saved execution logs"
                        style={{borderColor: '#d32f2f', color: '#d32f2f'}}
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '18px'}}>delete_forever</span>
                        Clear Logs
                      </button>
                    </div>
                    
                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', marginTop: '16px'}}>
                      {/* Summary Stats */}
                      <a 
                        href="/api/logs/summary" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#e8f4fd';
                          e.currentTarget.style.borderColor = '#1976d2';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#1976d2', fontSize: '24px'}}>summarize</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>Summary</div>
                          <div style={{fontSize: '12px', color: '#666'}}>Success/failure statistics</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>

                      {/* Full Analysis */}
                      <a 
                        href="/api/logs/analysis" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#e8f4fd';
                          e.currentTarget.style.borderColor = '#1976d2';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#1976d2', fontSize: '24px'}}>bar_chart</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>Full Analysis</div>
                          <div style={{fontSize: '12px', color: '#666'}}>Complete analysis report</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>

                      {/* Recent Failures */}
                      <a 
                        href="/api/logs/failures?limit=50" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#ffebee';
                          e.currentTarget.style.borderColor = '#d32f2f';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#d32f2f', fontSize: '24px'}}>error</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>Recent Failures</div>
                          <div style={{fontSize: '12px', color: '#666'}}>Last 50 failed executions</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>

                      {/* Unfixed Failures */}
                      <a 
                        href="/api/logs/failures?unfixed_only=true" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#fff3e0';
                          e.currentTarget.style.borderColor = '#f57c00';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#f57c00', fontSize: '24px'}}>warning</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>Unfixed Failures</div>
                          <div style={{fontSize: '12px', color: '#666'}}>Unresolved errors</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>

                      {/* Recent Successes */}
                      <a 
                        href="/api/logs/successes?limit=50" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#e8f5e9';
                          e.currentTarget.style.borderColor = '#388e3c';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#388e3c', fontSize: '24px'}}>check_circle</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>Recent Successes</div>
                          <div style={{fontSize: '12px', color: '#666'}}>Last 50 successful executions</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>

                      {/* Error Patterns */}
                      <a 
                        href="/api/logs/error-patterns" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#e8f4fd';
                          e.currentTarget.style.borderColor = '#1976d2';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#1976d2', fontSize: '24px'}}>troubleshoot</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>Error Patterns</div>
                          <div style={{fontSize: '12px', color: '#666'}}>Common error analysis</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>

                      {/* Recommendations */}
                      <a 
                        href="/api/logs/recommendations" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#f3e5f5';
                          e.currentTarget.style.borderColor = '#7b1fa2';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#7b1fa2', fontSize: '24px'}}>lightbulb</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>Recommendations</div>
                          <div style={{fontSize: '12px', color: '#666'}}>AI improvement suggestions</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>

                      {/* AI Context */}
                      <a 
                        href="/api/logs/ai-context?max_examples=10" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px 16px',
                          background: '#f5f5f5',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          color: '#333',
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#e8f4fd';
                          e.currentTarget.style.borderColor = '#1976d2';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#f5f5f5';
                          e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{color: '#1976d2', fontSize: '24px'}}>psychology</span>
                        <div style={{flex: 1}}>
                          <div style={{fontWeight: 500, fontSize: '14px'}}>AI Learning Context</div>
                          <div style={{fontSize: '12px', color: '#666'}}>What the AI has learned</div>
                        </div>
                        <span className="material-symbols-outlined" style={{color: '#999', fontSize: '18px'}}>open_in_new</span>
                      </a>
                    </div>

                    <div style={{marginTop: '16px', padding: '12px', background: '#e3f2fd', borderRadius: '8px', border: '1px solid #90caf9'}}>
                      <div style={{display: 'flex', gap: '8px', alignItems: 'start'}}>
                        <span className="material-symbols-outlined" style={{color: '#1976d2', fontSize: '20px'}}>info</span>
                        <div style={{fontSize: '13px', color: '#0d47a1'}}>
                          <strong>About Logging:</strong> The system automatically logs every script execution. 
                          Click any link above to view logs in JSON format. For a better viewing experience, use a browser extension 
                          like "JSON Viewer" or the CLI tool: <code style={{background: '#fff', padding: '2px 6px', borderRadius: '3px'}}>python analyze_logs.py summary</code>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Danger Zone */}
                <div className="settings-section">
                  <div className="md-card" style={{border: '1px solid #ffcdd2'}}>
                    <h3 className="settings-section-title" style={{color: '#b71c1c'}}>
                      <span className="material-symbols-outlined" style={{color: '#d32f2f', fontSize: '24px'}}>warning</span>
                      Danger Zone
                    </h3>
                    <p className="settings-section-description">
                      These actions permanently delete data and cannot be undone.
                    </p>

                    <div className="settings-info-box" style={{borderLeftColor: '#d32f2f'}}>
                      <div className="settings-info-header" style={{color: '#b71c1c'}}>
                        <span className="material-symbols-outlined" style={{color: '#d32f2f', fontSize: '20px'}}>delete_forever</span>
                        <strong>Reset All User Data</strong>
                      </div>
                      <p style={{marginTop: '8px', marginBottom: '0', color: '#5f2120'}}>
                        Deletes <strong>all user accounts</strong>, <strong>all user-saved scripts</strong>, and <strong>all user-uploaded images</strong>.
                        Default templates and default library images are kept.
                      </p>
                    </div>

                    <div style={{display: 'flex', justifyContent: 'flex-end', marginTop: '12px'}}>
                      <button
                        className="md-button md-button-outlined"
                        onClick={handleResetAllUserData}
                        title="Reset all user data (users, scripts, images)"
                        style={{borderColor: '#d32f2f', color: '#d32f2f'}}
                      >
                        <span className="material-symbols-outlined" style={{fontSize: '18px'}}>delete_forever</span>
                        Reset All User Data
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Help Tab */}
            {activeTab === 'help' && (
              <div className="maps-help-wrapper" style={{
                width: '100%',
                height: '100%',
                overflow: 'auto',
                background: isDark ? '#0f1115' : '#ffffff'
              }}>
                <style>{`
                  .maps-help-layout {
                    display: grid;
                    grid-template-columns: 260px minmax(0, 1fr);
                    width: 100%;
                    max-width: 1440px;
                    margin: 0 auto;
                    min-height: 100%;
                  }

                  .maps-help-nav {
                    border-right: 1px solid ${isDark ? '#2d3748' : '#d1d5db'};
                    background: ${isDark ? '#1a1f2e' : '#f3f4f6'};
                    padding: 16px 12px;
                    position: sticky;
                    top: 0;
                    max-height: 100vh;
                    overflow-y: auto;
                  }

                  .maps-help-main {
                    padding: 24px 28px 40px;
                    overflow-y: auto;
                    color: ${isDark ? '#e5e7eb' : '#111827'};
                  }

                  .maps-help h1, .maps-help h2, .maps-help h3, .maps-help h4 {
                    font-weight: 600;
                    letter-spacing: 0.01em;
                    color: ${isDark ? '#f3f4f6' : '#111827'};
                    margin-top: 0;
                  }

                  .maps-help h1 { font-size: 1.8rem; margin-bottom: 0.75rem; }
                  .maps-help h2 { font-size: 1.25rem; margin-top: 2rem; margin-bottom: 0.5rem; border-bottom: 1px solid ${isDark ? '#374151' : '#d1d5db'}; padding-bottom: 0.35rem; }
                  .maps-help h3 { font-size: 1.05rem; margin-top: 1.25rem; margin-bottom: 0.25rem; }

                  .maps-help p {color: ${isDark ? '#9ca3af' : '#4b5563'}; line-height: 1.6; margin: 0.35rem 0 0.75rem; font-size: 0.95rem; }
                  .maps-help ul, .maps-help ol { margin: 0.25rem 0 0.75rem 1.25rem; padding-left: 1rem; color: ${isDark ? '#9ca3af' : '#4b5563'}; font-size: 0.92rem; }
                  .maps-help li { margin-bottom: 0.15rem; }
                  .maps-help a { color: ${isDark ? '#60a5fa' : '#2563eb'}; text-decoration: none; }
                  .maps-help a:hover { text-decoration: underline; }

                  .maps-help .help-badge {
                    display: inline-block;
                    border-radius: 999px;
                    padding: 0.15rem 0.5rem;
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    background: ${isDark ? '#374151' : '#d1d5db'};
                    color: ${isDark ? '#9ca3af' : '#4b5563'};
                  }

                  .maps-help .help-badge-primary {
                    background: ${isDark ? 'rgba(96, 165, 250, 0.15)' : 'rgba(37, 99, 235, 0.12)'};
                    color: ${isDark ? '#60a5fa' : '#2563eb'};
                  }

                  .maps-help .help-subtitle { color: ${isDark ? '#9ca3af' : '#4b5563'}; font-size: 0.95rem; margin-bottom: 1.25rem; }

                  .maps-help .help-card {
                    background: ${isDark ? '#1a1f2e' : '#f3f4f6'};
                    border-radius: 12px;
                    border: 1px solid ${isDark ? '#374151' : '#d1d5db'};
                    padding: 12px 16px 14px;
                    margin-bottom: 12px;
                    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.15);
                  }

                  .maps-help .help-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
                  .maps-help .help-card-title { font-size: 0.95rem; font-weight: 600; color: ${isDark ? '#f3f4f6' : '#111827'}; }
                  .maps-help .help-card-body p:last-child { margin-bottom: 0; }

                  .maps-help .help-two-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 8px; }

                  .maps-help .help-nav-section-title {
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    letter-spacing: 0.11em;
                    color: ${isDark ? '#6b7280' : '#4b5563'};
                    margin: 18px 0 4px;
                    font-weight: 600;
                  }

                  .maps-help .help-nav-list { list-style: none; padding: 0; margin: 0; font-size: 0.87rem; }
                  .maps-help .help-nav-list li { margin-bottom: 2px; }
                  .maps-help .help-nav-list a {
                    display: block;
                    padding: 4px 4px;
                    border-radius: 6px;
                    color: ${isDark ? '#9ca3af' : '#4b5563'};
                  }
                  .maps-help .help-nav-list a:hover {
                    background: ${isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(37, 99, 235, 0.08)'};
                    color: ${isDark ? '#f3f4f6' : '#111827'};
                    text-decoration: none;
                  }

                  .maps-help pre {
                    background: ${isDark ? '#0d1117' : '#ffffff'};
                    border-radius: 8px;
                    padding: 8px 10px;
                    overflow-x: auto;
                    border: 1px solid ${isDark ? '#30363d' : '#d1d5db'};
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
                    font-size: 0.8rem;
                    line-height: 1.5;
                    margin: 0.4rem 0 0.8rem;
                    color: ${isDark ? '#c9d1d9' : '#24292f'};
                  }

                  .maps-help code {
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
                    font-size: 0.85rem;
                    background: ${isDark ? 'rgba(110, 118, 129, 0.2)' : 'rgba(175, 184, 193, 0.2)'};
                    padding: 0.15em 0.4em;
                    border-radius: 3px;
                  }

                  .maps-help pre code {
                    background: none;
                    padding: 0;
                  }

                  .maps-help .help-table-wrapper { overflow-x: auto; margin: 0.5rem 0 1rem; }
                  .maps-help table {
                    width: 100%;
                    border-collapse: collapse;
                    border-radius: 10px;
                    overflow: hidden;
                    font-size: 0.82rem;
                    background: ${isDark ? '#1a1f2e' : '#f3f4f6'};
                  }

                  .maps-help th, .maps-help td { padding: 8px 12px; text-align: left; border-bottom: 1px solid ${isDark ? '#374151' : '#d1d5db'}; }
                  .maps-help th { background: ${isDark ? '#252d3d' : '#e5e7eb'}; color: ${isDark ? '#f3f4f6' : '#111827'}; font-weight: 500; }
                  .maps-help tr:nth-child(even) td { background: ${isDark ? '#1a1f2e' : '#f3f4f6'}; }
                  .maps-help tr:nth-child(odd) td { background: ${isDark ? '#151922' : '#f9fafb'}; }

                  .maps-help .help-callout {
                    border-radius: 10px;
                    padding: 8px 10px;
                    margin: 0.5rem 0 0.9rem;
                    font-size: 0.85rem;
                    line-height: 1.4;
                    border: 1px solid ${isDark ? '#374151' : '#d1d5db'};
                    background: ${isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(37, 99, 235, 0.05)'};
                    color: ${isDark ? '#d1d5db' : '#4b5563'};
                  }

                  .maps-help .help-callout strong { color: ${isDark ? '#f3f4f6' : '#111827'}; }

                  .maps-help .help-callout.warn {
                    border-color: ${isDark ? '#92400e' : '#eab308'};
                    background: ${isDark ? 'rgba(234, 179, 8, 0.1)' : 'rgba(234, 179, 8, 0.1)'};
                  }

                  .maps-help .help-callout.error {
                    border-color: ${isDark ? '#991b1b' : '#f97373'};
                    background: ${isDark ? 'rgba(249, 115, 115, 0.1)' : 'rgba(254, 202, 202, 0.3)'};
                  }

                  @media (max-width: 900px) {
                    .maps-help-layout { grid-template-columns: 1fr; }
                    .maps-help-nav {
                      position: static;
                      max-height: none;
                      border-right: none;
                      border-bottom: 1px solid ${isDark ? '#2d3748' : '#d1d5db'};
                    }
                    .maps-help-main { padding: 16px 16px 32px; }
                  }
                `}</style>

                <div className="maps-help maps-help-layout">
                  {/* Navigation Sidebar */}
                  <nav className="maps-help-nav">
                    <h3 style={{marginTop:0, marginBottom:'0.1rem', color: isDark ? '#f3f4f6' : '#111827'}}>Help & Getting Started</h3>
                    <p style={{fontSize:'0.8rem', marginTop:'0.25rem', color: isDark ? '#9ca3af' : '#6b7280'}}>
                      Guidance for writing Python scripts that run in MAPS™ and the Helper App.
                    </p>

                    <div className="help-nav-section">
                      <div className="help-nav-section-title">Overview</div>
                      <ul className="help-nav-list">
                        <li><a href="#intro">Script Bridge & Helper App</a></li>
                        <li><a href="#core-concepts">Core Concepts</a></li>
                        <li><a href="#quick-start">Quick Start Template</a></li>
                      </ul>
                    </div>

                    <div className="help-nav-section">
                      <div className="help-nav-section-title">Helper App</div>
                      <ul className="help-nav-list">
                        <li><a href="#getting-started-app">Getting Started</a></li>
                        <li><a href="#ai-workflow">AI Code Assistant</a></li>
                        <li><a href="#running-scripts">Running Scripts</a></li>
                        <li><a href="#viewing-output">Viewing Output</a></li>
                        <li><a href="#image-library">Image Library</a></li>
                        <li><a href="#saving-scripts">Saving Scripts</a></li>
                        <li><a href="#quick-reference">Quick Reference</a></li>
                      </ul>
                    </div>

                    <div className="help-nav-section">
                      <div className="help-nav-section-title">Data Types</div>
                      <ul className="help-nav-list">
                        <li><a href="#tile-vs-layer">Tile Set vs Image Layer</a></li>
                      </ul>
                    </div>

                    <div className="help-nav-section">
                      <div className="help-nav-section-title">Patterns</div>
                      <ul className="help-nav-list">
                        <li><a href="#helpers">Helper Functions</a></li>
                        <li><a href="#output">Sending Output to MAPS</a></li>
                        <li><a href="#coords">Coordinate Helpers</a></li>
                        <li><a href="#defaults">Default Parameters</a></li>
                      </ul>
                    </div>

                    <div className="help-nav-section">
                      <div className="help-nav-section-title">Tips</div>
                      <ul className="help-nav-list">
                        <li><a href="#patterns">Common Patterns</a></li>
                        <li><a href="#mistakes">Common Mistakes</a></li>
                        <li><a href="#troubleshooting">Troubleshooting</a></li>
                        <li><a href="#why-helpers">Why Use Helpers?</a></li>
                      </ul>
                    </div>
                  </nav>

                  {/* Main Content */}
                  <main className="maps-help-main">
                    {/* INTRO / OVERVIEW */}
                    <section id="intro">
                      <span className="help-badge help-badge-primary">Overview</span>
                      <h1>MAPS Script Bridge & Helper App</h1>
                      <p className="help-subtitle">
                        Write Python scripts once and run them both in Thermo Fisher Scientific MAPS™ and in a local
                        Helper App, using the same MapsBridge API and AI-assisted workflow.
                      </p>

                      <div className="help-card">
                        <div className="help-card-header">
                          <div className="help-card-title">How the pieces fit together</div>
                        </div>
                        <div className="help-card-body">
                          <p>There are three main parts working together:</p>
                          <ul>
                            <li>
                              <strong>MAPS™</strong> – the microscope imaging and analysis application where
                              your scripts ultimately run and create real channels, layers, annotations, and tile sets.
                            </li>
                            <li>
                              <strong>MapsBridge.py (Script Bridge)</strong> – a small Python "SDK" that defines the
                              contract between MAPS and your scripts. It:
                              <ul>
                                <li>Reads requests (Tile Sets, Image Layers, parameters) from MAPS via <code>FromStdIn()</code></li>
                                <li>Exposes metadata (tiles, channels, stage positions, resolutions)</li>
                                <li>Provides functions to send images, annotations, notes, and files back into MAPS</li>
                              </ul>
                            </li>
                            <li>
                              <strong>Maps Python Script Helper App</strong> – a web-based IDE that simulates MAPS. It:
                              <ul>
                                <li>Feeds test requests into your script using the same MapsBridge protocol</li>
                                <li>Manages input / output folders and JSON payloads for you</li>
                                <li>Integrates an AI code assistant that generates and edits scripts based on this help</li>
                                <li>Includes preloaded example scripts and demo images (Tile Sets and Image Layers) you can run immediately</li>
                                <li>Shows logs and structured output (tile outputs, new layers, annotations, notes) in the UI</li>
                              </ul>
                            </li>
                          </ul>

                          <div className="help-callout">
                            <strong>Key idea:</strong> If a script uses <code>MapsBridge.py</code> correctly (no hard-coded
                            paths, no direct file I/O outside the API), it will behave the same in both the Helper App and MAPS.
                            The Helper App is your safe sandbox; MAPS is the production environment.
                          </div>
                        </div>
                      </div>

                      <div className="help-two-col">
                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">What is MapsBridge.py?</span>
                            <span className="help-badge">Core API</span>
                          </div>
                          <div className="help-card-body">
                            <p>
                              <code>MapsBridge.py</code> is the Script Bridge module that every MAPS script imports:
                            </p>
                            <pre><code>{`import MapsBridge

request = MapsBridge.ScriptTileSetRequest.FromStdIn()
tileSet = request.SourceTileSet`}</code></pre>
                            <p>
                              It defines the core data types (<code>TileSetInfo</code>, <code>ImageLayerInfo</code>, etc.)
                              and functions such as <code>CreateImageLayer</code>, <code>SendSingleTileOutput</code>,
                              <code>CreateAnnotation</code>, and more.
                            </p>
                            <p>
                              Your scripts should always talk to MAPS through these APIs, never by guessing file paths
                              or formats.
                            </p>
                          </div>
                        </div>

                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">What is the Helper App?</span>
                            <span className="help-badge">Development Tool</span>
                          </div>
                          <div className="help-card-body">
                            <p>
                              The Helper App is a local or web-hosted tool for developing MAPS scripts faster and with
                              less friction. At a glance, you can:
                            </p>
                            <ul>
                              <li><strong>Load preloaded example scripts</strong> (Tile Set, Image Layer, and demo patterns).</li>
                              <li><strong>Use preloaded demo images and datasets</strong> that ship with the app, so you can test scripts without hunting for data.</li>
                              <li><strong>Use the AI assistant panel</strong> to generate new scripts or refactor existing ones.</li>
                              <li><strong>Select a sample dataset</strong> to simulate MAPS Tile Sets or Image Layers.</li>
                              <li><strong>Run scripts</strong> and see logs, errors, and status in a console panel.</li>
                              <li><strong>View outputs</strong> in an output viewer (tile images, layers, annotations, notes).</li>
                              <li><strong>Copy or download the script</strong> once it works, and drop it into MAPS.</li>
                            </ul>
                            <p>
                              When a script is working correctly in the Helper App, you can move the same file into
                              MAPS with minimal or no changes and run it on real projects.
                            </p>
                          </div>
                        </div>
                      </div>
                    </section>

                    {/* Add a link to continue reading full documentation */}
                    <div className="help-callout" style={{marginTop: '24px'}}>
                      <strong>📚 Full Documentation:</strong> This is a condensed overview. Scroll down or use the navigation on the left to explore detailed sections including:
                      <ul style={{marginTop: '8px', marginBottom: 0}}>
                        <li>Core Concepts & Quick Start Template</li>
                        <li>Helper Functions & Coordinate Helpers</li>
                        <li>Common Patterns & Troubleshooting</li>
                        <li>AI Workflow & Best Practices</li>
                      </ul>
                    </div>

                    {/* CORE CONCEPTS */}
                    <section id="core-concepts">
                      <h2>Core Concepts</h2>

                      <div className="help-two-col">
                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">Script Inputs</span>
                            <span className="help-badge">Required</span>
                          </div>
                          <div className="help-card-body">
                            <p>Every script starts by reading a request from standard input via MapsBridge:</p>
                            <ul>
                              <li><code>ScriptTileSetRequest</code> – process tiles in a tile set</li>
                              <li><code>ScriptImageLayerRequest</code> – process a stitched image layer</li>
                              <li><code>ScriptRequest</code> – used in special cases</li>
                            </ul>
                            <pre><code>{`import MapsBridge

# Tile set script
request = MapsBridge.ScriptTileSetRequest.FromStdIn()
tileSet = request.SourceTileSet

# Image layer script
request = MapsBridge.ScriptImageLayerRequest.FromStdIn()
layer = request.SourceImageLayer`}</code></pre>
                          </div>
                        </div>

                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">Two Environments</span>
                          </div>
                          <div className="help-card-body">
                            <ul>
                              <li>
                                <strong>Helper App:</strong> Simulates MAPS, feeds JSON into your script, places images
                                in an input folder, and captures outputs for preview.
                              </li>
                              <li>
                                <strong>MAPS (Production):</strong> Runs the same script in a real MAPS project, uses
                                real tile set and layer data, and creates real channels, layers, and annotations.
                              </li>
                            </ul>
                            <div className="help-callout">
                              <strong>Key point:</strong> If you use MapsBridge APIs (and not hard-coded paths),
                              the same script runs in both environments.
                            </div>
                          </div>
                        </div>
                      </div>
                    </section>

                    {/* TILE VS LAYER */}
                    <section id="tile-vs-layer">
                      <h2>Tile Set vs Image Layer</h2>
                      <p>
                        MAPS supports two main data types for script processing:
                        <strong> Tile Sets</strong> (many tiles in a grid) and
                        <strong> Image Layers</strong> (single stitched image).
                      </p>

                      <div className="help-table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              <th>Feature</th>
                              <th>Tile Set</th>
                              <th>Image Layer</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td>Input</td>
                              <td>Many tiles in a grid (rows/columns)</td>
                              <td>One large stitched image</td>
                            </tr>
                            <tr>
                              <td>Primary class</td>
                              <td><code>ScriptTileSetRequest</code></td>
                              <td><code>ScriptImageLayerRequest</code></td>
                            </tr>
                            <tr>
                              <td>Images accessed via</td>
                              <td><code>tileInfo.ImageFileNames["0"]</code> + DataFolderPath</td>
                              <td><code>request.PreparedImages["0"]</code></td>
                            </tr>
                            <tr>
                              <td>Typical usage</td>
                              <td>Per-tile analysis, per-tile QA, acquisition workflows</td>
                              <td>Whole-image segmentation, overlays, heatmaps</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>

                    {/* QUICK START */}
                    <section id="quick-start">
                      <h2>Quick Start Script Template</h2>
                      <p>This is a recommended starting template for a single-tile processing script.</p>

                      <pre><code>{`import MapsBridge
from PIL import Image
import os

def main():
    # Read request (Tile Set, single-tile mode)
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    tileSet = request.SourceTileSet

    # Resolve tile + TileInfo + path for channel "0"
    tile, tileInfo, input_path = MapsBridge.ResolveSingleTileAndPath(request, "0")

    MapsBridge.LogInfo(f"Processing tile [{tile.Row}, {tile.Column}]")

    # Load and process image
    img = Image.open(input_path)
    out_img = img  # TODO: replace with your logic

    # Save output to a temp folder
    out_dir = MapsBridge.GetTempOutputFolder("my_script")
    out_path = os.path.join(out_dir, "result.png")
    out_img.save(out_path)

    # Create/reuse output tile set & channel "Processed"
    outInfo = MapsBridge.GetDefaultOutputTileSetAndChannel(
        sourceTileSet=tileSet,
        channelName="Processed",
        channelColor=(255, 0, 0),
        isAdditive=True,
        targetLayerGroupName="Outputs"
    )

    # Send result back into MAPS
    MapsBridge.SendSingleTileOutput(
        tileRow=tile.Row,
        tileColumn=tile.Column,
        targetChannelName="Processed",
        imageFilePath=out_path,
        keepFile=True,
        targetTileSetGuid=outInfo.TileSet.Guid
    )

    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()`}</code></pre>
                    </section>

                    {/* HELPERS */}
                    <section id="helpers">
                      <h2>MapsBridge Helper Functions</h2>
                      <p>
                        Your updated <code>MapsBridge.py</code> includes several helper functions designed to remove
                        boilerplate and reduce errors in scripts.
                      </p>

                      <h3>Single-tile resolution</h3>
                      <pre><code>{`# Returns (Tile, TileInfo, image_path) for channel "0"
tile, tileInfo, input_path = MapsBridge.ResolveSingleTileAndPath(request, "0")`}</code></pre>

                      <h3>Batch iteration helpers</h3>
                      <pre><code>{`# Iterate over ALL tiles in a TileSet
for tileInfo, path in MapsBridge.IterTileInfosWithPath(tileSet, "0"):
    ...

# Iterate only over TilesToProcess in a ScriptTileSetRequest
for tile, tileInfo, path in MapsBridge.IterTilesToProcessWithPath(request, "0"):
    ...`}</code></pre>

                      <h3>Image layer helper</h3>
                      <pre><code>{`# For ScriptImageLayerRequest
path = MapsBridge.GetPreparedImagePath(request, "0")`}</code></pre>

                      <h3>Script parameter parsing</h3>
                      <pre><code>{`options = MapsBridge.ParseScriptParameters(request.ScriptParameters)

# JSON example:
#   "{ "sigma": 5, "threshold": 0.8 }"
# key/value example:
#   "sigma=5; threshold=0.8; mode=fast"

sigma = float(options.get("sigma", 5))`}</code></pre>

                      <h3>Standard temp output folder</h3>
                      <pre><code>{`out_dir = MapsBridge.GetTempOutputFolder("MyScript")`}</code></pre>

                      <h3>Default output tile set & channel</h3>
                      <pre><code>{`outInfo = MapsBridge.GetDefaultOutputTileSetAndChannel(
    sourceTileSet=tileSet,
    channelName="Processed",
    channelColor=(255, 0, 0),
    isAdditive=True,
    targetLayerGroupName="Outputs"
)`}</code></pre>
                    </section>

                    {/* OUTPUT */}
                    <section id="output">
                      <h2>Sending Output Back to MAPS</h2>

                      <h3>Tile output</h3>
                      <pre><code>{`MapsBridge.SendSingleTileOutput(
    tileRow=tile.Row,
    tileColumn=tile.Column,
    targetChannelName="Processed",
    imageFilePath=output_path,
    keepFile=True,
    targetTileSetGuid=outputTileSet.Guid  # or None for source tile set
)`}</code></pre>

                      <h3>Create or reuse an Output Tile Set</h3>
                      <pre><code>{`outInfo = MapsBridge.GetOrCreateOutputTileSet(
    tileSetName="Results for " + tileSet.Name,
    targetLayerGroupName="Outputs"
)`}</code></pre>

                      <h3>Create channels</h3>
                      <pre><code>{`MapsBridge.CreateChannel(
    "Processed",
    (255, 0, 0),
    True,
    outInfo.TileSet.Guid
)`}</code></pre>

                      <h3>Create a new image layer</h3>
                      <pre><code>{`MapsBridge.CreateImageLayer(
    "Processed " + layer.Name,
    imageFilePath=output_path,
    targetLayerGroupName="Outputs",
    keepFile=True
)`}</code></pre>

                      <h3>Annotations</h3>
                      <pre><code>{`MapsBridge.CreateAnnotation(
    "Feature_001",
    stagePosition=(0.001, 0.002, 0),
    size=("10um", "5um"),
    color=(0, 255, 0),
    notes="Region of interest",
    targetLayerGroupName="Annotations"
)`}</code></pre>

                      <h3>Notes and files</h3>
                      <pre><code>{`# Append notes to a layer/tile set
MapsBridge.AppendNotes(
    "Processed tile [1, 1]\\r\\n",
    targetLayerGuid=outInfo.TileSet.Guid
)

# Store a report or arbitrary file
MapsBridge.StoreFile(
    "C:\\\\analysis\\\\report.pdf",
    overwrite=True,
    keepFile=True,
    targetLayerGuid=outInfo.TileSet.Guid
)`}</code></pre>
                    </section>

                    {/* COORDINATES */}
                    <section id="coords">
                      <h2>Coordinate Helpers</h2>
                      <p>
                        Use these to convert from image pixel coordinates to stage coordinates, instead of
                        implementing your own transform logic.
                      </p>

                      <h3>Tile pixel → stage</h3>
                      <pre><code>{`stagePos = MapsBridge.TilePixelToStage(
    pixelX, pixelY,
    tile.Column, tile.Row,
    tileSet
)
# stagePos.X, stagePos.Y in stage units`}</code></pre>

                      <h3>Image layer pixel → stage</h3>
                      <pre><code>{`stagePos = MapsBridge.ImagePixelToStage(pixelX, pixelY, imageLayer)`}</code></pre>
                    </section>

                    {/* DEFAULT PARAMS */}
                    <section id="defaults">
                      <h2>Default Parameters Block</h2>
                      <p>
                        Each script can define default parameters that MAPS reads and passes into the script.
                      </p>

                      <pre><code>{`# Default parameters
#{
#  "RunMode": "manual",
#  "ScriptMode": "singletiles",
#  "PrepareImages": true,
#  "ScriptParameters": "120",
#  "StopOnError": true
#}
# Default parameters end`}</code></pre>

                      <p>
                        The <code>ScriptParameters</code> field is a free-form string that your script can parse using
                        <code> MapsBridge.ParseScriptParameters()</code> (JSON or <code>key=value</code> notation).
                      </p>
                    </section>

                    {/* HELPER APP: GETTING STARTED */}
                    <section id="getting-started-app">
                      <h2>Getting Started with the Helper App</h2>
                      <p>
                        The Maps Python Script Helper App is designed to make it easy to iterate on MapsBridge-based
                        scripts with fast feedback and AI assistance.
                      </p>

                      <div className="help-two-col">
                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">Typical workflow</span>
                          </div>
                          <div className="help-card-body">
                            <ol>
                              <li>Open the Helper App in your browser.</li>
                              <li>Load a preloaded example script (Tile Set, Image Layer, or demo) or create a new script.</li>
                              <li>Select one of the preloaded demo datasets (example Tile Sets or Image Layers) to simulate a MAPS project.</li>
                              <li>Click <strong>Run</strong> to execute the script with synthetic MAPS requests using those images.</li>
                              <li>View logs, outputs, and any annotations or new tile sets requested by your script.</li>
                              <li>Use the AI assistant to fix errors, improve structure, or add new functionality.</li>
                              <li>Once satisfied, copy the script into MAPS and run it on a real project.</li>
                            </ol>
                          </div>
                        </div>

                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">What the Helper App simulates</span>
                          </div>
                          <div className="help-card-body">
                            <ul>
                              <li>JSON payloads sent from MAPS to your script.</li>
                              <li>Standard input / output wiring with <code>FromStdIn()</code>.</li>
                              <li>DataFolderPath and PreparedImages behavior.</li>
                              <li>Logging via <code>LogInfo</code>, <code>LogWarning</code>, and <code>LogError</code>.</li>
                              <li>Output actions: tile output, layer creation, annotations, notes, and stored files.</li>
                            </ul>
                            <div className="help-callout warn">
                              <strong>Note:</strong> The Helper App does not drive the microscope itself, but it accurately
                              simulates what MAPS will send to your script and how your script's responses will be interpreted.
                            </div>
                          </div>
                        </div>
                      </div>
                    </section>

                    {/* AI WORKFLOW */}
                    <section id="ai-workflow">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                        <MapsAILogo size={60} showText={false} />
                        <h2 style={{ marginTop: 0, marginBottom: 0 }}>AI Code Assistant Workflow</h2>
                      </div>
                      <p>
                        The Helper App includes an AI code assistant that is primed with this help content and the
                        MapsBridge API. You can use it to:
                      </p>
                      <ul>
                        <li>Generate new scripts from plain language descriptions.</li>
                        <li>Refactor older scripts to use the new helper functions.</li>
                        <li>Convert exploratory code into production-style MAPS scripts.</li>
                        <li>Explain complex scripts step by step.</li>
                      </ul>

                      <div className="help-card">
                        <div className="help-card-header">
                          <span className="help-card-title">Example AI prompts</span>
                        </div>
                        <div className="help-card-body">
                          <ul>
                            <li>
                              <strong>"Create a single-tile script that thresholds SE images and outputs a binary mask in a new channel."</strong>
                            </li>
                            <li>
                              <strong>"Refactor this older script to use ResolveSingleTileAndPath and GetDefaultOutputTileSetAndChannel."</strong>
                            </li>
                            <li>
                              <strong>"Add batch processing to this script using IterTilesToProcessWithPath."</strong>
                            </li>
                            <li>
                              <strong>"Explain how TilePixelToStage is converting pixel coordinates in this code."</strong>
                            </li>
                          </ul>
                          <p>
                            The assistant knows that scripts must use MapsBridge APIs for I/O and should avoid hard-coded
                            paths or MAPS-internal assumptions.
                          </p>
                        </div>
                      </div>

                      <div className="help-callout">
                        <strong>Pro tip:</strong> The AI can automatically see your current code and any errors from the last run.
                        Just ask "Why did my script fail?" or "Fix this error" without pasting anything.
                      </div>
                    </section>

                    {/* RUNNING SCRIPTS */}
                    <section id="running-scripts">
                      <h2>Running Scripts in the Helper App</h2>
                      <p>
                        The Helper App executes your scripts in a secure, sandboxed Docker container that simulates
                        the MAPS environment.
                      </p>

                      <div className="help-two-col">
                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">Step-by-step: Running a script</span>
                          </div>
                          <div className="help-card-body">
                            <ol>
                              <li>Load or write a script in the <strong>Python</strong> tab</li>
                              <li>Go to the <strong>Image Library</strong> tab and select a test image (click on an image card)</li>
                              <li>Return to the <strong>Python</strong> tab</li>
                              <li>Click the green <strong>Run</strong> button in the left panel</li>
                              <li>Wait for execution (typically 5-30 seconds)</li>
                              <li>Switch to the <strong>Output</strong> tab to see results</li>
                            </ol>
                            <p>
                              If no image is selected, you'll be prompted to choose one from a modal dialog.
                            </p>
                          </div>
                        </div>

                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">What happens during execution</span>
                          </div>
                          <div className="help-card-body">
                            <ol>
                              <li>Your code is sent to the backend server</li>
                              <li>A Docker container starts with Python + common libraries (PIL, NumPy, OpenCV, scikit-image)</li>
                              <li>Your selected test image is mounted into the container</li>
                              <li>A synthetic MAPS request (JSON) is generated and piped to your script's stdin</li>
                              <li>Your script executes (max 5 minutes timeout)</li>
                              <li>All output files, logs, and errors are collected</li>
                              <li>Results are displayed in the Output tab</li>
                              <li>Container is destroyed</li>
                            </ol>
                          </div>
                        </div>
                      </div>

                      <h3>Execution environment</h3>
                      <p>Scripts run in a sandboxed environment with:</p>
                      <ul>
                        <li><strong>Pre-installed libraries:</strong> PIL/Pillow, NumPy, OpenCV (cv2), scikit-image, scipy, matplotlib, pandas</li>
                        <li><strong>Timeout:</strong> 5 minutes maximum execution time</li>
                        <li><strong>Isolation:</strong> No network access, no access to your local file system (except through MapsBridge APIs)</li>
                        <li><strong>Temporary storage:</strong> All files are cleared after execution</li>
                      </ul>

                      <div className="help-callout warn">
                        <strong>Important:</strong> Scripts cannot access your local file system directly. Always use
                        MapsBridge helper functions like <code>ResolveSingleTileAndPath()</code> and <code>GetTempOutputFolder()</code>
                        to work with files.
                      </div>

                      <h3>Stopping a running script</h3>
                      <p>
                        If a script is taking too long or needs to be stopped, click the red <strong>Stop</strong> button
                        that appears while the script is running. The Docker container will be terminated immediately.
                      </p>
                    </section>

                    {/* VIEWING OUTPUT */}
                    <section id="viewing-output">
                      <h2>Viewing Script Output</h2>
                      <p>
                        After running a script, switch to the <strong>Output</strong> tab to see results. The output
                        panel has three main sections:
                      </p>

                      <h3>1. Console Output</h3>
                      <div className="help-card">
                        <div className="help-card-body">
                          <p>The console shows all text output from your script:</p>
                          <ul>
                            <li><code>MapsBridge.LogInfo()</code>, <code>LogWarning()</code>, <code>LogError()</code> messages</li>
                            <li>Python <code>print()</code> statements</li>
                            <li>Error messages and stack traces</li>
                            <li>Execution status ("Running...", "Script completed successfully", "Script failed")</li>
                          </ul>
                          <p>
                            <strong>Color coding:</strong> Info messages appear in white/gray, warnings in yellow,
                            and errors in red for easy scanning.
                          </p>
                        </div>
                      </div>

                      <h3>2. Image Output</h3>
                      <div className="help-card">
                        <div className="help-card-body">
                          <p>Images are displayed in a grid layout:</p>
                          <ul>
                            <li><strong>Original Image:</strong> Your input test image (shown for reference)</li>
                            <li><strong>Result Images:</strong> Any images created by your script via <code>SendSingleTileOutput()</code> or <code>CreateImageLayer()</code></li>
                          </ul>
                          <p>
                            <strong>Image Viewer:</strong> Click on any image to open the full-size viewer with:
                          </p>
                          <ul>
                            <li><strong>Mouse wheel:</strong> Zoom in/out</li>
                            <li><strong>Click and drag:</strong> Pan around the image</li>
                            <li><strong>Zoom buttons:</strong> +/- for precise zoom control</li>
                            <li><strong>Reset button:</strong> Return to 100% zoom and center</li>
                            <li><strong>Zoom indicator:</strong> Shows current zoom percentage</li>
                          </ul>
                        </div>
                      </div>

                      <h3>3. File Output</h3>
                      <div className="help-card">
                        <div className="help-card-body">
                          <p>Non-image files created by your script appear as downloadable file icons:</p>
                          <ul>
                            <li>CSV files (data tables)</li>
                            <li>JSON files (structured data)</li>
                            <li>TXT files (reports, logs)</li>
                            <li>PDF files (documents)</li>
                            <li>Any other files created via <code>StoreFile()</code></li>
                          </ul>
                          <p>Click on a file icon to download it to your computer.</p>
                        </div>
                      </div>

                      <h3>Understanding errors</h3>
                      <div className="help-callout error">
                        <strong>Common error: KeyError: '0'</strong><br />
                        Your script tried to access a channel that doesn't exist. Always use string keys
                        (<code>"0"</code> not <code>0</code>) and ensure <code>"PrepareImages": true</code> in default parameters.
                      </div>

                      <div className="help-callout error">
                        <strong>Common error: FileNotFoundError</strong><br />
                        The image path is incorrect. Use MapsBridge helpers like <code>ResolveSingleTileAndPath()</code>
                        instead of hardcoded paths.
                      </div>

                      <div className="help-callout warn">
                        <strong>Timeout after 5 minutes</strong><br />
                        Your script took too long. Optimize the algorithm or test with smaller images.
                      </div>
                    </section>

                    {/* IMAGE LIBRARY */}
                    <section id="image-library">
                      <h2>Working with the Image Library</h2>
                      <p>
                        The Image Library tab manages test images used to run and validate your scripts.
                      </p>

                      <h3>Uploading images</h3>
                      <div className="help-card">
                        <div className="help-card-body">
                          <ol>
                            <li>Go to the <strong>Image Library</strong> tab</li>
                            <li>Click the <strong>Upload Image</strong> button</li>
                            <li>In the upload dialog:
                              <ul>
                                <li><strong>Image File:</strong> Click to select or drag-and-drop (PNG, JPEG, TIFF, etc.)</li>
                                <li><strong>Name:</strong> Give it a descriptive name (auto-filled from filename)</li>
                                <li><strong>Description:</strong> Optional details about the image</li>
                                <li><strong>Type:</strong> Select SEM, SDB, TEM, or Optical</li>
                              </ul>
                            </li>
                            <li>Click <strong>Upload</strong></li>
                          </ol>
                          <div className="help-callout">
                            <strong>Supported formats:</strong> PNG, JPEG, TIFF, GIF, BMP, and most common image formats.
                            Maximum file size is typically 50MB.
                          </div>
                        </div>
                      </div>

                      <h3>Image types</h3>
                      <div className="help-table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              <th>Type</th>
                              <th>Color Badge</th>
                              <th>Description</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td><strong>SEM</strong></td>
                              <td>Blue</td>
                              <td>Scanning Electron Microscope images</td>
                            </tr>
                            <tr>
                              <td><strong>SDB</strong></td>
                              <td>Green</td>
                              <td>Stem Darkfield / Backscatter images</td>
                            </tr>
                            <tr>
                              <td><strong>TEM</strong></td>
                              <td>Orange</td>
                              <td>Transmission Electron Microscope images</td>
                            </tr>
                            <tr>
                              <td><strong>Optical</strong></td>
                              <td>Purple</td>
                              <td>Light microscopy images</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>

                      <h3>Managing your library</h3>
                      <ul>
                        <li><strong>Select an image:</strong> Click on an image card to mark it as selected (blue border appears)</li>
                        <li><strong>View full-size:</strong> Click the zoom icon on an image card to view in the image viewer</li>
                        <li><strong>Delete an image:</strong> Click the trash icon and confirm</li>
                      </ul>

                      <div className="help-callout">
                        <strong>Best practice:</strong> Upload diverse test images (different sizes, content, quality levels)
                        to thoroughly test your scripts before deploying to MAPS. Include challenging cases like noisy images,
                        low contrast, or images with artifacts.
                      </div>
                    </section>

                    {/* SAVING SCRIPTS */}
                    <section id="saving-scripts">
                      <h2>Saving & Managing Scripts</h2>
                      <p>
                        The Helper App provides two ways to save your scripts: <strong>Save</strong> and <strong>Save As</strong>.
                      </p>

                      <h3>Save vs Save As</h3>
                      <div className="help-two-col">
                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">Save button</span>
                          </div>
                          <div className="help-card-body">
                            <p>Behavior depends on what's currently loaded:</p>
                            <ul>
                              <li><strong>New/unsaved script:</strong> Opens save dialog to create a new script</li>
                              <li><strong>Your saved script:</strong> Updates the existing script immediately (no dialog)</li>
                              <li><strong>Default template:</strong> Opens save dialog to save as a new script</li>
                            </ul>
                          </div>
                        </div>

                        <div className="help-card">
                          <div className="help-card-header">
                            <span className="help-card-title">Save As button</span>
                          </div>
                          <div className="help-card-body">
                            <p>Always opens the save dialog to create a new script.</p>
                            <ul>
                              <li>Useful for creating variations of existing scripts</li>
                              <li>Useful for creating versioned copies (v1, v2, v3)</li>
                              <li>Pre-fills the name with "scriptname v2" for convenience</li>
                            </ul>
                          </div>
                        </div>
                      </div>

                      <h3>Save dialog fields</h3>
                      <ul>
                        <li><strong>Name</strong> (required): Short descriptive name for your script</li>
                        <li><strong>Description</strong> (optional): Detailed explanation of what the script does</li>
                        <li><strong>Category</strong> (optional): Organize scripts by type (Template, Image Processing, Analysis, Advanced, Utility)</li>
                      </ul>

                      <h3>Accessing your saved scripts</h3>
                      <ol>
                        <li>Go to the <strong>Scripts</strong> tab</li>
                        <li>Click <strong>My Scripts</strong> (top sub-tab)</li>
                        <li>Your saved scripts appear as cards, grouped by category</li>
                        <li>Click a script card to load it into the editor</li>
                        <li>Use the trash icon to delete scripts you no longer need</li>
                      </ol>

                      <div className="help-callout">
                        <strong>Version control tip:</strong> Use "Save As" with version suffixes like "My Script v2", "My Script v3"
                        and add change notes in the Description field. This helps track different versions and what changed.
                      </div>
                    </section>

                    {/* QUICK REFERENCE */}
                    <section id="quick-reference">
                      <h2>Quick Reference: Common Tasks</h2>

                      <div className="help-card">
                        <div className="help-card-header">
                          <span className="help-card-title">Task: Start a new script from a template</span>
                        </div>
                        <div className="help-card-body">
                          <ol>
                            <li>Go to <strong>Scripts</strong> tab → <strong>Default Templates</strong></li>
                            <li>Click on a template that matches your needs</li>
                            <li>Modify the code in the <strong>Python</strong> tab</li>
                            <li>Click <strong>Save Script</strong> to save to My Scripts</li>
                          </ol>
                        </div>
                      </div>

                      <div className="help-card">
                        <div className="help-card-header">
                          <span className="help-card-title">Task: Test a script on an image</span>
                        </div>
                        <div className="help-card-body">
                          <ol>
                            <li>Upload or select an image in <strong>Image Library</strong> tab</li>
                            <li>Load or write a script in <strong>Python</strong> tab</li>
                            <li>Click <strong>Run</strong> button</li>
                            <li>View results in <strong>Output</strong> tab</li>
                          </ol>
                        </div>
                      </div>

                      <div className="help-card">
                        <div className="help-card-header">
                          <span className="help-card-title">Task: Debug a failing script</span>
                        </div>
                        <div className="help-card-body">
                          <ol>
                            <li>Run the script and let it fail</li>
                            <li>Check the error message in the <strong>Output</strong> tab console</li>
                            <li>Open the <strong>AI Assistant</strong> panel (visible in Python tab)</li>
                            <li>Ask: "Why did my script fail?" or "Fix this error"</li>
                            <li>The AI can see your code and the error automatically</li>
                            <li>Apply the AI's suggestions and run again</li>
                          </ol>
                        </div>
                      </div>

                      <div className="help-card">
                        <div className="help-card-header">
                          <span className="help-card-title">Task: Deploy a tested script to MAPS</span>
                        </div>
                        <div className="help-card-body">
                          <ol>
                            <li>Test your script thoroughly with multiple images</li>
                            <li>In the <strong>Python</strong> tab, select all code (Ctrl+A)</li>
                            <li>Copy to clipboard (Ctrl+C)</li>
                            <li>Open MAPS → Tools → Scripts → New Python Script</li>
                            <li>Paste your code</li>
                            <li>Save the script in MAPS with a descriptive name</li>
                            <li>Test on a single tile first before running on full datasets</li>
                          </ol>
                        </div>
                      </div>

                      <div className="help-card">
                        <div className="help-card-header">
                          <span className="help-card-title">Task: Get AI help writing a new script</span>
                        </div>
                        <div className="help-card-body">
                          <ol>
                            <li>AI Assistant uses server-configured API keys</li>
                            <li>Open the <strong>AI Assistant</strong> panel</li>
                            <li>Describe what you want: "Create a script that detects edges using Canny and outputs to a new channel called 'Edges'"</li>
                            <li>Review the generated code</li>
                            <li>Test it with a sample image</li>
                            <li>Ask follow-up questions to refine: "Add a parameter to control the threshold"</li>
                          </ol>
                        </div>
                      </div>
                    </section>

                    {/* PATTERNS */}
                    <section id="patterns">
                      <h2>Common Patterns</h2>

                      <h3>Single-tile processing</h3>
                      <pre><code>{`request = MapsBridge.ScriptTileSetRequest.FromStdIn()
tile, tileInfo, path = MapsBridge.ResolveSingleTileAndPath(request, "0")`}</code></pre>

                      <h3>Batch tile processing (all tiles)</h3>
                      <pre><code>{`tileSet = request.SourceTileSet
for tileInfo, path in MapsBridge.IterTileInfosWithPath(tileSet, "0"):
    ...`}</code></pre>

                      <h3>Batch tile processing (TilesToProcess only)</h3>
                      <pre><code>{`for tile, tileInfo, path in MapsBridge.IterTilesToProcessWithPath(request, "0"):
    ...`}</code></pre>

                      <h3>Stitched Image Layer</h3>
                      <pre><code>{`request = MapsBridge.ScriptImageLayerRequest.FromStdIn()
layer = request.SourceImageLayer
path = MapsBridge.GetPreparedImagePath(request, "0")`}</code></pre>

                      <h3>Scheduling new acquisitions</h3>
                      <pre><code>{`MapsBridge.CreateTileSet(
    "New Acquisition",
    stagePosition=(tile.StagePosition.X, tile.StagePosition.Y, tileSet.Rotation),
    totalSize=("30um", "20um"),
    tileHfw="5um",
    pixelSize="4nm",
    scheduleAcquisition=True,
    targetLayerGroupName="New Acquisitions"
)`}</code></pre>
                    </section>

                    {/* MISTAKES */}
                    <section id="mistakes">
                      <h2>Common Mistakes</h2>

                      <div className="help-callout error">
                        <strong>1. Using integer channel indices.</strong><br />
                        Always use string keys:
                        <code> ImageFileNames["0"]</code>, <code>PreparedImages["0"]</code> — never <code>0</code> without quotes.
                      </div>

                      <div className="help-callout warn">
                        <strong>2. Hardcoding input/output paths.</strong><br />
                        Use the paths given by MapsBridge (DataFolderPath, PreparedImages) and
                        <code> GetTempOutputFolder()</code> rather than manual paths.
                      </div>

                      <div className="help-callout warn">
                        <strong>3. Forgetting to create a channel before sending output.</strong><br />
                        <code>SendSingleTileOutput</code> will not create the channel automatically.
                      </div>

                      <div className="help-callout">
                        <strong>4. Not using helpers.</strong><br />
                        Helpers like <code>ResolveSingleTileAndPath</code> and
                        <code> GetDefaultOutputTileSetAndChannel</code> encode best practices and reduce mistakes.
                      </div>
                    </section>

                    {/* TROUBLESHOOTING */}
                    <section id="troubleshooting">
                      <h2>Troubleshooting</h2>

                      <h3>"Tile not found" when using TilePixelToStage or helpers</h3>
                      <p>
                        Make sure the <code>tile.Column</code> and <code>tile.Row</code> values you pass actually exist
                        in the <code>TileSetInfo.Tiles</code> list. If you manually construct a <code>Tile</code>, ensure
                        the indices match the source tile set.
                      </p>

                      <h3>"No prepared image for channel '0'"</h3>
                      <p>
                        For image layer scripts, you must have <code>"PrepareImages": true</code> in the default parameters.
                        The helper will raise a <code>KeyError</code> if the channel is missing.
                      </p>

                      <h3>Output tile set is None</h3>
                      <p>
                        This indicates that MAPS or the Helper App failed to create or locate the tile set. Check logs
                        from the host application for more information.
                      </p>
                    </section>

                    {/* WHY HELPERS */}
                    <section id="why-helpers">
                      <h2>Why Use Helper Functions?</h2>
                      <p>
                        The convenience helpers in <code>MapsBridge.py</code> are designed to:
                      </p>
                      <ul>
                        <li>Eliminate repetitive boilerplate (path construction, tile lookups)</li>
                        <li>Enforce best practices (string channel keys, correct tile resolution)</li>
                        <li>Make scripts shorter, clearer, and easier to maintain</li>
                        <li>Help AI-based script generators produce correct code more reliably</li>
                      </ul>
                      <p>
                        For small one-off scripts, the core API is enough. For any script used repeatedly or shared across
                        teams, helpers give you consistency and fewer bugs.
                      </p>
                    </section>
                  </main>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Resizer Handle - Only show for Code/Output/Welcome */}
        {(activeTab === 'code' || activeTab === 'output' || activeTab === 'welcome') && (
          <div 
            className="assistant-resizer"
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
            style={{ cursor: 'col-resize' }}
          />
        )}

        {/* Assistant Sidebar - Only show for Code/Output/Welcome */}
        {(activeTab === 'code' || activeTab === 'output' || activeTab === 'welcome') && (
          <div className="assistant-sidebar" style={{ width: `${assistantWidth}px` }}>
          <div className="assistant-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MapsAILogo size={32} showText={false} />
              <h3 style={{ margin: 0 }}>AI Assistant</h3>
            </div>
            <div className="assistant-header-actions">
              <button 
                className="new-chat-button"
                onClick={() => {
                  setMessages([]);
                  setAiModel('gemini-2.5-flash-lite'); // Reset to default model
                  // Clear code editor
                  if (monacoEditorRef.current) {
                    monacoEditorRef.current.setValue('');
                  }
                  setCode('');
                  // Clear any stored errors
                  setLastError(null);
                }}
                title="Start new chat and clear code"
              >
                <span className="material-symbols-outlined">add</span>
                New Chat
              </button>
            </div>
          </div>
          <div className="assistant-settings-panel">
            <label htmlFor="ai-model-select" className="assistant-settings-label">AI Model</label>
            <select
              id="ai-model-select"
              className="assistant-settings-select"
              value={aiModel}
              onChange={(e) => handleModelChange(e.target.value)}
            >
              <option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite (fast)</option>
              <option value="gemini-2.5-pro">gemini-2.5-pro (best quality)</option>
            </select>
          </div>
          <div className="assistant-messages" ref={messagesContainerRef}>
            {messages.length === 0 ? (
              <div className="welcome-message">
                <div className="welcome-content">
                  <div style={{ marginBottom: '20px' }}>
                    <MapsAILogo size={180} showText={true} />
                  </div>
                  <p style={{ marginTop: '24px', fontSize: '15px' }}>I'm here to help you with electron microscopy data visualization and Python scripting for the MAPS interface.</p>
                  <p style={{ fontSize: '15px' }}>Ask me anything about your code or images!</p>
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.type} ${msg.isLoading ? 'loading' : ''}`}>
                  {msg.isLoading ? (
                    <div className="thinking-animation">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <span className="thinking-text">AI is thinking...</span>
                    </div>
                  ) : (
                    <>
                      <div className="message-content" dangerouslySetInnerHTML={{ __html: formatMessage(msg.text) }} />
                      {msg.quickReplies && msg.quickReplies.length > 0 && (
                        <div className="quick-replies">
                          {msg.quickReplies.map((reply, replyIdx) => (
                            <button
                              key={replyIdx}
                              className="quick-reply-button"
                              onClick={async () => {
                                // Some quick replies are UI-only actions (e.g., dismiss)
                                if (reply && reply.action === 'dismiss') {
                                  setMessages(prev => prev.map((m, i) => (
                                    i === idx ? { ...m, quickReplies: null } : m
                                  )));
                                  return;
                                }

                                // SendText allows short button labels but richer sent content
                                // Ensure we always get a string, never an object
                                let quickReplyText = '';
                                if (reply && reply.sendText) {
                                  quickReplyText = String(reply.sendText);
                                } else if (reply && reply.text) {
                                  quickReplyText = String(reply.text);
                                } else if (typeof reply === 'string') {
                                  quickReplyText = reply;
                                } else {
                                  console.error('Invalid quick reply format:', reply);
                                  quickReplyText = 'Quick reply';
                                }

                                // Clear quick replies after click to prevent double-submits
                                const baseMessages = messages.map((m, i) => (
                                  i === idx ? { ...m, quickReplies: null } : m
                                ));

                                const newMessages = [...baseMessages, { type: 'user', text: quickReplyText }];
                                setMessages(newMessages);
                                setMessageInput('');
                                
                                // Add loading message
                                const loadingMessages = [...newMessages, { type: 'assistant', text: '', isLoading: true }];
                                setMessages(loadingMessages);
                                
                                try {
                                  const currentCode = monacoEditorRef.current ? monacoEditorRef.current.getValue() : code;
                                  const imageUrl = selectedImage || null;
                                  
                                  let contextParts = [];
                                  if (currentCode) {
                                    contextParts.push(`Current code:\n${currentCode.substring(0, 8000)}`);
                                  }
                                  if (lastError) {
                                    contextParts.push(`\n\nLast execution error:\n${lastError.message}`);
                                    if (lastError.stderr && lastError.stderr !== '(no error output)') {
                                      contextParts.push(`\nSTDERR:\n${lastError.stderr}`);
                                    }
                                    if (lastError.stdout && lastError.stdout !== '(no output)') {
                                      contextParts.push(`\nSTDOUT:\n${lastError.stdout}`);
                                    }
                                  }
                                  
                                  const response = await fetch('/api/chat', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      messages: newMessages.map(m => ({ 
                                        role: m.type === 'user' ? 'user' : 'assistant', 
                                        content: typeof m.text === 'string' ? m.text : String(m.text || '')
                                      })),
                                      context: contextParts.length > 0 ? contextParts.join('\n') : null,
                                      image_url: imageUrl,
                                      model: aiModel
                                    })
                                  });
                                  
                                  const data = await response.json();
                                  
                                  if (data.success) {
                                    const assistantMessage = { type: 'assistant', text: data.response || '', quickReplies: data.quick_replies || null };
                                    
                                    console.log('[MapsScriptHelper] [QUICK REPLY] AI Response received:');
                                    console.log('[MapsScriptHelper] [QUICK REPLY]   - Response text length:', (data.response || '').length);
                                    console.log('[MapsScriptHelper] [QUICK REPLY]   - Has suggested_code:', !!data.suggested_code);
                                    if (data.suggested_code) {
                                      console.log('[MapsScriptHelper] [QUICK REPLY]   - Code length:', data.suggested_code.length);
                                    }
                                    
                                    // Handle code updates with robust logic
                                    if (data.suggested_code && data.suggested_code.trim()) {
                                      const codeToSet = data.suggested_code.trim();
                                      let updateSuccess = false;
                                      
                                      // Get current code to compare
                                      let currentCode = '';
                                      if (monacoEditorRef.current) {
                                        currentCode = monacoEditorRef.current.getValue().trim();
                                      } else {
                                        currentCode = code.trim();
                                      }
                                      
                                      // Only update if the code is actually different
                                      const codeChanged = currentCode !== codeToSet;
                                      
                                      if (monacoEditorRef.current) {
                                        try {
                                          console.log('[MapsScriptHelper] [QUICK REPLY] Updating code...');
                                          
                                          // Use executeEdits for better reliability
                                          const model = monacoEditorRef.current.getModel();
                                          if (model) {
                                            const fullRange = model.getFullModelRange();
                                            monacoEditorRef.current.executeEdits('ai-update', [{
                                              range: fullRange,
                                              text: codeToSet,
                                              forceMoveMarkers: true
                                            }]);
                                          } else {
                                            monacoEditorRef.current.setValue(codeToSet);
                                          }
                                          
                                          // Small delay for Monaco to process
                                          await new Promise(resolve => setTimeout(resolve, 50));
                                          
                                          // Verify the update worked
                                          const verifyCode = monacoEditorRef.current.getValue();
                                          if (verifyCode === codeToSet || verifyCode.trim() === codeToSet.trim()) {
                                            setCode(codeToSet);
                                            updateSuccess = true;
                                            if (codeChanged) {
                                              if (!assistantMessage.text.includes('✅ Code has been updated')) {
                                                assistantMessage.text += '\n\n✅ Code has been updated in the editor!';
                                              }
                                              console.log('[MapsScriptHelper] ✓ [QUICK REPLY] Code updated successfully');
                                              animateCodeUpdate();
                                            }
                                          } else {
                                            console.error('[MapsScriptHelper] [QUICK REPLY] Verification failed, retrying...');
                                            // Retry with setValue
                                            monacoEditorRef.current.setValue(codeToSet);
                                            await new Promise(resolve => setTimeout(resolve, 50));
                                            const verifyCode2 = monacoEditorRef.current.getValue();
                                            if (verifyCode2 === codeToSet || verifyCode2.trim() === codeToSet.trim()) {
                                              setCode(codeToSet);
                                              updateSuccess = true;
                                              if (codeChanged) {
                                                if (!assistantMessage.text.includes('✅ Code has been updated')) {
                                                  assistantMessage.text += '\n\n✅ Code has been updated (retry succeeded)!';
                                                }
                                                animateCodeUpdate();
                                              }
                                            } else {
                                              setCode(codeToSet);
                                              updateSuccess = false;
                                              if (!assistantMessage.text.includes('Code has been updated')) {
                                                assistantMessage.text += '\n\n⚠️ Code update may have failed. Please check the editor.';
                                              }
                                            }
                                          }
                                        } catch (error) {
                                          console.error('[MapsScriptHelper] [QUICK REPLY] Update error:', error);
                                          setCode(codeToSet);
                                          updateSuccess = false;
                                          if (!assistantMessage.text.includes('Code has been updated')) {
                                            assistantMessage.text += '\n\n⚠️ Code update error. Please copy manually.';
                                          }
                                        }
                                      } else {
                                        console.warn('[MapsScriptHelper] [QUICK REPLY] Monaco not available');
                                        setCode(codeToSet);
                                        updateSuccess = true;
                                        if (codeChanged) {
                                          if (!assistantMessage.text.includes('✅ Code has been updated')) {
                                            assistantMessage.text += '\n\n✅ Code state updated (editor will sync)!';
                                          }
                                        }
                                      }

                                      // If we're on the Welcome screen, jump to the editor to show the generated code
                                      if (activeTab === 'welcome') {
                                        setCurrentScript(null);
                                        setActiveTab('code');
                                        setEditorKey(prev => prev + 1);
                                      }
                                    } else {
                                      console.log('[MapsScriptHelper] [QUICK REPLY] ℹ️ No code update - AI response was text-only');
                                    }
                                    
                                    setMessages([...newMessages, assistantMessage]);
                                  } else {
                                    setMessages([...newMessages, { type: 'assistant', text: data.error || 'Sorry, I encountered an error.' }]);
                                  }
                                } catch (error) {
                                  setMessages([...newMessages, { type: 'assistant', text: `Sorry, I could not connect to the AI service: ${error.message}` }]);
                                }
                              }}
                              title={reply.description}
                            >
                              <span className="material-symbols-outlined">{reply.icon}</span>
                              <span className="quick-reply-text">{reply.text}</span>
                              <span className="quick-reply-description">{reply.description}</span>
                            </button>
                          ))}
                        </div>
                      )}
                      {msg.type === 'assistant' && !msg.quickReplies && msg.text.includes('✅ Code has been updated') && (
                        <div className="message-actions">
                          <button
                            className="rerun-code-button"
                            onClick={handleRun}
                            disabled={isRunning}
                            title="Rerun code"
                          >
                            <span className="material-symbols-outlined">play_arrow</span>
                            {isRunning ? 'Running...' : 'Rerun Code'}
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="assistant-input-container">
            <textarea
              ref={textareaRef}
              className="md-textfield md-textarea"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Message AI Assistant..."
              rows="1"
            />
            <button 
              className="assistant-send-btn"
              onClick={handleSendMessage}
              disabled={!messageInput.trim()}
              title="Send message (Enter)"
            >
              <span className="material-symbols-outlined">arrow_upward</span>
            </button>
          </div>
        </div>
        )}
      </div>

      {/* Image Viewer Modal - Available from all tabs */}
      <ImageViewerModal
        isOpen={showImageViewer}
        image={viewerImage}
        onClose={() => {
          setShowImageViewer(false);
          setViewerImage(null);
        }}
        isDark={isDark}
      />

      {/* Toast Notification */}
      {toast && (
        <div className={`toast-notification ${toast.type}`}>
          <span className="material-symbols-outlined toast-icon">
            {toast.type === 'success' ? 'check_circle' : 'error'}
          </span>
          <span className="toast-message">{toast.message}</span>
        </div>
      )}
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));


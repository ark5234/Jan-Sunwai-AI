import React, { useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css'; // Standard import, though global linked in html too

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [userName, setUserName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [complaintText, setComplaintText] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
  };

  const handleAnalyze = async () => {
    if (!file || !userName) {
      alert("Please upload an image and enter your name.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('username', userName);

    try {
      const response = await axios.post('http://localhost:8000/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setResult(response.data);
      setComplaintText(response.data.generated_complaint);
    } catch (error) {
      console.error("Error analyzing image:", error);
      alert("An error occurred during analysis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Jan-Sunwai AI</h1>
      <p>Automated Civic Grievance Reporting</p>

      <div className="card">
        <h3>1. Report Details</h3>
        <input 
          type="text" 
          placeholder="Your Name" 
          value={userName} 
          onChange={(e) => setUserName(e.target.value)} 
          style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
        />
        <input type="file" onChange={handleFileChange} accept="image/*" />
        
        {preview && (
          <div style={{ marginTop: '10px' }}>
            <img src={preview} alt="Preview" style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '4px' }} />
          </div>
        )}

        {file && !loading && (
          <button onClick={handleAnalyze} className="btn" style={{ marginTop: '10px' }}>
            Analyze Complaint
          </button>
        )}
        
        {loading && <p>AI is analyzing the image and drafting your complaint...</p>}
      </div>

      {result && (
        <div className="card">
          <h3>2. AI Analysis Result</h3>
          <p><strong>Department:</strong> {result.classification.department}</p>
          <p><strong>Detected Issue:</strong> {result.classification.description}</p>
          <p><strong>Confidence:</strong> {result.classification.confidence}</p>
          
          <h4>Location</h4>
          <p>{result.location.address}</p>
          
          {result.location.coordinates && (
             <div style={{ height: '300px', width: '100%', marginBottom: '20px' }}>
               <MapContainer center={[result.location.coordinates.lat, result.location.coordinates.lon]} zoom={13} style={{ height: '100%', width: '100%' }}>
                 <TileLayer
                   url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                 />
                 <Marker position={[result.location.coordinates.lat, result.location.coordinates.lon]}>
                   <Popup>Incident Location</Popup>
                 </Marker>
               </MapContainer>
             </div>
          )}

          <h3>3. Drafted Complaint</h3>
          <textarea 
            value={complaintText} 
            onChange={(e) => setComplaintText(e.target.value)}
            style={{ width: '100%', height: '200px', padding: '10px' }}
          />
          <button className="btn" style={{ marginTop: '10px' }}>Submit Complaint</button>
        </div>
      )}
    </div>
  );
}

export default App;

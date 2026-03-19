import React, { useState } from 'react';
import StarMap from './StarMap';
import axios from 'axios';

function App() {
  const [name, setName] = useState('JISHNU');
  const [date, setDate] = useState('2026-03-15');
  const [time, setTime] = useState('20:00');
  const [latitude, setLatitude] = useState('13.0');
  const [longitude, setLongitude] = useState('77.7');
  const [constellationData, setConstellationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateConstellation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:5000/api/constellation', {
        name,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        date,
        time
      });
      
      setConstellationData(response.data);
    } catch (err) {
      setError('Failed to generate constellation. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const useCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLatitude(position.coords.latitude.toFixed(4));
          setLongitude(position.coords.longitude.toFixed(4));
        },
        (err) => {
          setError('Could not get your location: ' + err.message);
        }
      );
    } else {
      setError('Geolocation is not supported by your browser');
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>✨ Personal Constellation Generator</h1>
      <p style={styles.subtitle}>Create constellations from real stars visible from your location</p>
      
      <div style={styles.controlPanel}>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Your Name:</label>
          <input
            style={styles.input}
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value.toUpperCase())}
            placeholder="Enter name"
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>Date:</label>
          <input
            style={styles.input}
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>Time:</label>
          <input
            style={styles.input}
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>Latitude:</label>
          <input
            style={styles.input}
            type="number"
            step="0.1"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>Longitude:</label>
          <input
            style={styles.input}
            type="number"
            step="0.1"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
          />
        </div>
        
        <div style={styles.buttonGroup}>
          <button style={styles.button} onClick={useCurrentLocation}>
            📍 Use My Location
          </button>
          <button 
            style={{...styles.button, ...styles.primaryButton}} 
            onClick={generateConstellation}
            disabled={loading}
          >
            {loading ? '✨ Generating...' : '✨ Create My Constellation'}
          </button>
        </div>
        
        {error && <div style={styles.error}>{error}</div>}
      </div>
      
      {constellationData && (
        <div style={styles.stats}>
          <p>
            <strong>{constellationData.name}</strong> constellation • 
            {constellationData.star_count} stars used • 
            {constellationData.total_visible_stars} stars visible
          </p>
          <p style={styles.small}>
            {new Date(constellationData.datetime).toLocaleString()} • 
            Lat: {constellationData.location.lat}°, Lon: {constellationData.location.lon}°
          </p>
        </div>
      )}
      
      <div style={styles.mapContainer}>
        <StarMap constellationData={constellationData} />
      </div>
    </div>
  );
}

const styles = {
  container: {
    fontFamily: 'Arial, sans-serif',
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto',
    backgroundColor: '#0a0a2a',
    color: 'white',
    minHeight: '100vh'
  },
  title: {
    fontSize: '2.5em',
    marginBottom: '5px',
    color: '#ffd700'
  },
  subtitle: {
    fontSize: '1.1em',
    marginBottom: '30px',
    color: '#aaccff'
  },
  controlPanel: {
    backgroundColor: '#1a1a3a',
    padding: '20px',
    borderRadius: '10px',
    marginBottom: '20px',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '15px'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column'
  },
  label: {
    marginBottom: '5px',
    fontSize: '0.9em',
    color: '#aaccff'
  },
  input: {
    padding: '8px',
    borderRadius: '5px',
    border: '1px solid #334466',
    backgroundColor: '#0a0a2a',
    color: 'white'
  },
  buttonGroup: {
    gridColumn: '1 / -1',
    display: 'flex',
    gap: '10px',
    justifyContent: 'center',
    marginTop: '10px'
  },
  button: {
    padding: '10px 20px',
    borderRadius: '5px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1em',
    transition: 'all 0.3s',
    backgroundColor: '#334466',
    color: 'white'
  },
  primaryButton: {
    backgroundColor: '#ffd700',
    color: '#0a0a2a',
    fontWeight: 'bold'
  },
  error: {
    gridColumn: '1 / -1',
    color: '#ff6b6b',
    padding: '10px',
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    borderRadius: '5px'
  },
  stats: {
    marginBottom: '20px',
    padding: '10px',
    backgroundColor: '#1a1a3a',
    borderRadius: '5px'
  },
  small: {
    fontSize: '0.8em',
    color: '#aaccff'
  },
  mapContainer: {
    height: '500px',
    border: '2px solid #334466',
    borderRadius: '10px',
    overflow: 'hidden'
  }
};

export default App;
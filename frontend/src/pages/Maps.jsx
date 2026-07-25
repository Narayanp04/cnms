import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import { mapsAPI } from '../services/api'
import L from 'leaflet'

// Fix default marker icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

export default function Maps() {
  const [features, setFeatures] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const { data } = await mapsAPI.getDevices()
      setFeatures(data.features || [])
    } catch (err) {
      console.error('Failed to load map data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>
  }

  const statusIcons = {
    UP: L.divIcon({
      className: 'custom-marker',
      html: '<div style="width:16px;height:16px;background:#22c55e;border:2px solid white;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.3)"></div>',
    }),
    DOWN: L.divIcon({
      className: 'custom-marker',
      html: '<div style="width:16px;height:16px;background:#ef4444;border:2px solid white;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.3);animation:pulse 2s infinite"></div>',
    }),
    Warning: L.divIcon({
      className: 'custom-marker',
      html: '<div style="width:16px;height:16px;background:#eab308;border:2px solid white;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.3)"></div>',
    }),
  }

  const defaultCenter = features.length > 0 
    ? [features[0].geometry.coordinates[1], features[0].geometry.coordinates[0]]
    : [20, 0]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Network Map</h1>
          <p className="text-sm text-gray-500">{features.length} devices shown on map</p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-success-500"></div> UP</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-danger-500"></div> DOWN</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-warning-500"></div> Warning</div>
        </div>
      </div>

      <div className="card overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
        <MapContainer
          center={defaultCenter}
          zoom={3}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {features.map(f => (
            <Marker
              key={f.properties.id}
              position={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
              icon={statusIcons[f.properties.status] || statusIcons.UP}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold text-base mb-1">{f.properties.hostname}</p>
                  <p className="text-gray-600 mb-2">{f.properties.ip_address}</p>
                  <div className="space-y-1">
                    <p><strong>Status:</strong> {f.properties.status}</p>
                    <p><strong>Latency:</strong> {f.properties.latency}</p>
                    <p><strong>Packet Loss:</strong> {f.properties.packet_loss}</p>
                    <p><strong>Customer:</strong> {f.properties.customer}</p>
                    <p><strong>Site:</strong> {f.properties.site}</p>
                    <p><strong>Provider:</strong> {f.properties.provider}</p>
                    <p><strong>SLA 24h:</strong> {f.properties.sla_24h}</p>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}

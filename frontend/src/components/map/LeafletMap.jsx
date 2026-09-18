import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export const LeafletMap = ({ 
  geoJsonData, 
  crimeLocation, 
  filterCategory = 'all', 
  selectedAtmId = null,
  onSelectAtm = () => {} 
}) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const defaultCenter = crimeLocation 
        ? [crimeLocation.lat, crimeLocation.lng] 
        : [12.9352, 77.6245];

      const map = L.map(mapContainerRef.current, {
        center: defaultCenter,
        zoom: 14,
        zoomControl: false
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // Dark Matter tactical tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(map);

      mapInstanceRef.current = map;
      markersLayerRef.current = L.layerGroup().addTo(map);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Markers and Layers when data or filters change
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layer = markersLayerRef.current;
    if (!map || !layer) return;

    layer.clearLayers();

    // 1. Plot Crime Epicenter if available
    if (crimeLocation) {
      const crimeCenter = [crimeLocation.lat, crimeLocation.lng];

      // Epicenter marker with restrained styling
      const crimeIcon = L.divIcon({
        className: 'crime-pin',
        html: `
          <div class="relative flex items-center justify-center">
            <div class="w-5 h-5 rounded-md bg-indigo-600 border border-white shadow-md flex items-center justify-center text-[10px] font-bold text-white">
              ✕
            </div>
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      const crimeMarker = L.marker(crimeCenter, { icon: crimeIcon })
        .bindPopup(`
          <div class="p-2 space-y-1 font-sans">
            <div class="text-[11px] font-mono font-bold text-indigo-400 uppercase">REPORTED CRIME ORIGIN</div>
            <div class="text-xs font-semibold text-slate-100">${crimeLocation.crime_type || 'Cybercrime Incident'}</div>
            <div class="text-[11px] text-slate-300">Amount: ₹${crimeLocation.amount ? crimeLocation.amount.toLocaleString('en-IN') : 'N/A'}</div>
            <div class="text-[10px] font-mono text-slate-400">Lat: ${crimeLocation.lat}, Lng: ${crimeLocation.lng}</div>
          </div>
        `);
      layer.addLayer(crimeMarker);

      // 3km candidate search radius circle
      const radiusCircle = L.circle(crimeCenter, {
        radius: 3000,
        color: '#6366f1',
        weight: 1.5,
        dashArray: '4, 8',
        fillColor: '#6366f1',
        fillOpacity: 0.04
      });
      layer.addLayer(radiusCircle);

      map.panTo(crimeCenter);
    }

    // 2. Plot ATM GeoJSON Features
    if (geoJsonData && geoJsonData.features) {
      geoJsonData.features.forEach((feature) => {
        const props = feature.properties || {};
        const coords = feature.geometry.coordinates; // [lng, lat]
        const latLng = [coords[1], coords[0]];

        // Apply risk filter
        if (filterCategory !== 'all' && props.risk_category !== filterCategory) {
          return;
        }

        const isSelected = selectedAtmId === props.atm_id;

        // Determine pin colors
        const colorMap = {
          high: { bg: '#ef4444', text: '#fee2e2' },
          medium: { bg: '#f59e0b', text: '#fef3c7' },
          low: { bg: '#3b82f6', text: '#dbeafe' }
        };

        const theme = colorMap[props.risk_category] || colorMap.low;
        const scorePercent = Math.round((props.risk_score || 0) * 100);

        const atmPin = L.divIcon({
          className: 'atm-marker-pin',
          html: `
            <div class="relative flex items-center justify-center cursor-pointer transition-transform hover:scale-105">
              <div class="px-1.5 py-0.5 rounded-md font-mono text-[11px] font-bold border shadow-md flex items-center gap-1 ${isSelected ? 'ring-2 ring-white' : ''}" 
                   style="background-color: #090d16; border-color: ${theme.bg}; color: ${theme.text};">
                <span class="w-2 h-2 rounded-sm" style="background-color: ${theme.bg};"></span>
                <span>${scorePercent}%</span>
              </div>
            </div>
          `,
          iconSize: [44, 24],
          iconAnchor: [22, 12]
        });

        const marker = L.marker(latLng, { icon: atmPin });

        // Popup content matching contracts without em dashes
        const explanationsHtml = (props.explanation || [])
          .map(e => `<li class="text-[11px] text-slate-300">• ${e}</li>`)
          .join('');

        const windowStart = props.predicted_window?.start 
          ? new Date(props.predicted_window.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : 'N/A';
        const windowEnd = props.predicted_window?.end 
          ? new Date(props.predicted_window.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : 'N/A';

        marker.bindPopup(`
          <div class="p-2.5 min-w-[220px] font-sans space-y-2">
            <div class="flex items-center justify-between border-b border-slate-700 pb-1.5">
              <span class="text-[11px] font-mono font-bold text-slate-400 uppercase">${props.atm_id}</span>
              <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded uppercase" 
                    style="background-color: ${theme.bg}22; color: ${theme.bg}; border: 1px solid ${theme.bg}55;">
                ${props.risk_category} RISK
              </span>
            </div>

            <div>
              <div class="text-sm font-bold text-white">${props.bank || 'Candidate ATM'}</div>
              <div class="text-xs text-slate-400">${props.area || 'Bangalore Urban'}</div>
            </div>

            <div class="grid grid-cols-2 gap-2 py-1.5 bg-slate-900 rounded-md p-2 border border-slate-800 font-mono text-[11px]">
              <div>
                <div class="text-slate-400 text-[10px]">RISK SCORE</div>
                <div class="font-bold text-slate-100">${(props.risk_score * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div class="text-slate-400 text-[10px]">CONFIDENCE</div>
                <div class="font-bold text-slate-100">${(props.confidence * 100).toFixed(1)}%</div>
              </div>
            </div>

            <div class="text-[11px] text-slate-300">
              <span class="text-slate-400 text-[10px] uppercase font-mono block">6-HR PREDICTED WINDOW:</span>
              <span class="font-mono text-indigo-300">${windowStart} to ${windowEnd}</span>
            </div>

            ${explanationsHtml ? `
              <div class="pt-1.5 border-t border-slate-800">
                <span class="text-[10px] text-slate-400 uppercase font-mono block mb-1">Key Signals:</span>
                <ul class="space-y-0.5">${explanationsHtml}</ul>
              </div>
            ` : ''}
          </div>
        `);

        marker.on('click', () => {
          onSelectAtm(props.atm_id);
        });

        layer.addLayer(marker);
      });
    }
  }, [geoJsonData, crimeLocation, filterCategory, selectedAtmId]);

  return (
    <div className="relative w-full h-full min-h-[480px] rounded-xl overflow-hidden border border-slate-800 shadow-md">
      <div ref={mapContainerRef} className="w-full h-full min-h-[480px]" />
    </div>
  );
};

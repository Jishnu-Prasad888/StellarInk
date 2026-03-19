import React, { useRef, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, Text, Billboard } from '@react-three/drei';
import * as THREE from 'three';

// ── colour helper: blue-white for hot stars, yellow-orange for cooler ──────
function starColor(mag) {
  const t = Math.max(0, Math.min(1, (mag + 1) / 7));
  return new THREE.Color().setHSL(0.6 - t * 0.15, 0.8, 0.65 + t * 0.1);
}

// ── one constellation star sphere + optional name label ───────────────────
function ConstellationStar({ x, y, mag, name, letter, showNames }) {
  const radius = Math.max(0.06, 0.22 - mag * 0.025);
  const color  = starColor(mag);

  return (
    <group position={[x, y, 0]}>
      {/* glow halo */}
      <mesh>
        <sphereGeometry args={[radius * 2.2, 8, 8]} />
        <meshBasicMaterial color={color} transparent opacity={0.12} />
      </mesh>
      {/* star core */}
      <mesh>
        <sphereGeometry args={[radius, 12, 12]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={1.2}
        />
      </mesh>
      {/* name label */}
      {showNames && (
        <Billboard follow lockX={false} lockY={false} lockZ={false}>
          <Text
            position={[0, radius + 0.28, 0]}
            fontSize={0.28}
            color="#e8d8ff"
            anchorX="center"
            anchorY="bottom"
            outlineWidth={0.015}
            outlineColor="#000022"
          >
            {name}
          </Text>
          {/* letter badge */}
          <Text
            position={[0, radius + 0.62, 0]}
            fontSize={0.22}
            color="#ffd700"
            anchorX="center"
            anchorY="bottom"
            outlineWidth={0.012}
            outlineColor="#000022"
          >
            [{letter}]
          </Text>
        </Billboard>
      )}
    </group>
  );
}

// ── constellation lines ────────────────────────────────────────────────────
function ConstellationLines({ connections, positions }) {
  const geometry = useMemo(() => {
    const pts = [];
    connections.forEach(([i, j]) => {
      if (positions[i] && positions[j]) {
        pts.push(new THREE.Vector3(...positions[i]));
        pts.push(new THREE.Vector3(...positions[j]));
      }
    });
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, [connections, positions]);

  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color="#ffd700" transparent opacity={0.75} linewidth={2} />
    </lineSegments>
  );
}

// ── main scene ─────────────────────────────────────────────────────────────
function ConstellationScene({ constellationData, showNames }) {
  const stars       = constellationData?.constellation_stars ?? [];
  const connections = constellationData?.connections          ?? [];
  const name        = constellationData?.name                 ?? '';

  // Map result-array index → 3-D position
  const positions = useMemo(
    () =>
      stars.map(s => [
        (s.x_norm - 0.5) * 22,
        (s.y_norm - 0.5) * 14,
        0,
      ]),
    [stars]
  );

  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[0, 10, 10]} intensity={0.6} />

      {/* Milky-way-like background stars */}
      <Stars radius={120} depth={60} count={3000} factor={3.5} saturation={0.1} fade />

      {/* Letter label at the top */}
      {name && (
        <Text
          position={[0, 9.5, 0]}
          fontSize={1.2}
          color="#ffd700"
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.05}
          outlineColor="#000033"
        >
          {name}
        </Text>
      )}

      {/* Constellation lines drawn first (behind stars) */}
      <ConstellationLines connections={connections} positions={positions} />

      {/* Stars */}
      {stars.map((star, i) => (
        <ConstellationStar
          key={i}
          x={positions[i][0]}
          y={positions[i][1]}
          mag={star.mag}
          name={star.star_name ?? `HIP ${star.hip_id}`}
          letter={star.letter ?? ''}
          showNames={showNames}
        />
      ))}

      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        autoRotate
        autoRotateSpeed={0.4}
        minDistance={5}
        maxDistance={80}
      />
    </>
  );
}

// ── exported component ─────────────────────────────────────────────────────
export default function StarMap({ constellationData }) {
  const [showNames, setShowNames] = React.useState(true);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* toggle button */}
      <button
        onClick={() => setShowNames(v => !v)}
        style={{
          position: 'absolute',
          top: 10,
          right: 12,
          zIndex: 10,
          padding: '6px 14px',
          background: showNames ? '#ffd700' : '#334466',
          color: showNames ? '#0a0a2a' : '#ffffff',
          border: 'none',
          borderRadius: 6,
          cursor: 'pointer',
          fontSize: '0.85em',
          fontWeight: 'bold',
        }}
      >
        {showNames ? '★ Hide Names' : '★ Show Names'}
      </button>

      <Canvas camera={{ position: [0, 0, 28], fov: 55 }}>
        <ConstellationScene
          constellationData={constellationData}
          showNames={showNames}
        />
      </Canvas>
    </div>
  );
}
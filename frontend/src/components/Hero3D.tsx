import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import * as THREE from 'three';

type StarData = {
  positions: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
  twinkleOffsets: Float32Array;
  count: number;
};

function generateStars(count: number, minRadius: number, maxRadius: number, sizeRange: [number, number]): StarData {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const twinkleOffsets = new Float32Array(count);

  const starColors = [
    [0.6, 0.7, 1.0],
    [0.8, 0.85, 1.0],
    [1.0, 1.0, 1.0],
    [1.0, 0.95, 0.85],
    [1.0, 0.85, 0.7],
    [1.0, 0.7, 0.5],
  ];

  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const radius = minRadius + Math.random() * (maxRadius - minRadius);

    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = radius * Math.cos(phi);

    const colorWeight = Math.random();
    let colorIndex: number;
    if (colorWeight < 0.05) colorIndex = 0;
    else if (colorWeight < 0.15) colorIndex = 1;
    else if (colorWeight < 0.45) colorIndex = 2;
    else if (colorWeight < 0.75) colorIndex = 3;
    else if (colorWeight < 0.9) colorIndex = 4;
    else colorIndex = 5;

    const [r, g, b] = starColors[colorIndex];
    colors[i * 3] = r * (0.9 + Math.random() * 0.2);
    colors[i * 3 + 1] = g * (0.9 + Math.random() * 0.2);
    colors[i * 3 + 2] = b * (0.9 + Math.random() * 0.2);

    const magnitude = Math.pow(Math.random(), 2.5);
    sizes[i] = sizeRange[0] + magnitude * (sizeRange[1] - sizeRange[0]);

    twinkleOffsets[i] = Math.random() * Math.PI * 2;
  }

  return { positions, colors, sizes, twinkleOffsets, count };
}

function Starfield() {
  const pointsRef = useRef<THREE.Points>(null);
  const brightPointsRef = useRef<THREE.Points>(null);

  const dimStars = useMemo(() => generateStars(2500, 30, 80, [0.3, 1.2]), []);
  const mediumStars = useMemo(() => generateStars(800, 20, 50, [0.8, 2.0]), []);
  const brightStars = useMemo(() => generateStars(150, 15, 40, [1.5, 3.5]), []);

  const backgroundStars = useMemo(() => {
    const totalCount = dimStars.count + mediumStars.count;
    const positions = new Float32Array(totalCount * 3);
    const colors = new Float32Array(totalCount * 3);
    const sizes = new Float32Array(totalCount);

    positions.set(dimStars.positions);
    positions.set(mediumStars.positions, dimStars.count * 3);
    colors.set(dimStars.colors);
    colors.set(mediumStars.colors, dimStars.count * 3);
    sizes.set(dimStars.sizes);
    sizes.set(mediumStars.sizes, dimStars.count);

    return { positions, colors, sizes, count: totalCount };
  }, [dimStars, mediumStars]);

  useFrame((state) => {
    if (!brightPointsRef.current) return;
    const t = state.clock.getElapsedTime();
    const geo = brightPointsRef.current.geometry;
    const sizeAttr = geo.getAttribute('size') as THREE.BufferAttribute;

    for (let i = 0; i < brightStars.count; i++) {
      const baseSize = brightStars.sizes[i];
      const twinkle = Math.sin(t * (1.5 + Math.random() * 0.5) + brightStars.twinkleOffsets[i]) * 0.3 + 0.85;
      sizeAttr.setX(i, baseSize * twinkle);
    }
    sizeAttr.needsUpdate = true;
  });

  return (
    <group>
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={backgroundStars.count}
            array={backgroundStars.positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={backgroundStars.count}
            array={backgroundStars.colors}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-size"
            count={backgroundStars.count}
            array={backgroundStars.sizes}
            itemSize={1}
          />
        </bufferGeometry>
        <pointsMaterial
          vertexColors
          size={1}
          sizeAttenuation
          transparent
          opacity={0.9}
          depthWrite={false}
        />
      </points>

      <points ref={brightPointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={brightStars.count}
            array={brightStars.positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={brightStars.count}
            array={brightStars.colors}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-size"
            count={brightStars.count}
            array={brightStars.sizes}
            itemSize={1}
          />
        </bufferGeometry>
        <pointsMaterial
          vertexColors
          size={2}
          sizeAttenuation
          transparent
          opacity={1}
          depthWrite={false}
        />
      </points>
    </group>
  );
}

function Moon() {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  const moonTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d')!;

    ctx.fillStyle = '#c9c5c0';
    ctx.fillRect(0, 0, 512, 512);

    const imageData = ctx.getImageData(0, 0, 512, 512);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      const noise = (Math.random() - 0.5) * 20;
      data[i] = Math.max(0, Math.min(255, data[i] + noise));
      data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
      data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
    }
    ctx.putImageData(imageData, 0, 0);

    const drawCrater = (x: number, y: number, radius: number, darkness: number) => {
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      gradient.addColorStop(0, `rgba(80, 75, 70, ${darkness})`);
      gradient.addColorStop(0.7, `rgba(100, 95, 90, ${darkness * 0.6})`);
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();
    };

    drawCrater(180, 150, 80, 0.4);
    drawCrater(280, 200, 60, 0.35);
    drawCrater(150, 280, 50, 0.3);
    drawCrater(320, 320, 70, 0.35);
    drawCrater(220, 350, 45, 0.3);

    for (let i = 0; i < 40; i++) {
      const x = Math.random() * 512;
      const y = Math.random() * 512;
      const r = 5 + Math.random() * 25;
      const d = 0.15 + Math.random() * 0.2;
      drawCrater(x, y, r, d);
    }

    for (let i = 0; i < 100; i++) {
      const x = Math.random() * 512;
      const y = Math.random() * 512;
      const r = 2 + Math.random() * 8;
      drawCrater(x, y, r, 0.1 + Math.random() * 0.15);
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.getElapsedTime();
    groupRef.current.rotation.y = t * 0.01;

    if (glowRef.current) {
      const material = glowRef.current.material as THREE.MeshBasicMaterial;
      material.opacity = 0.12 + Math.sin(t * 0.5) * 0.03;
    }
  });

  return (
    <group ref={groupRef} position={[3.2, 1.8, -8]}>
      <mesh ref={glowRef} scale={1.3}>
        <sphereGeometry args={[0.18, 32, 32]} />
        <meshBasicMaterial color="#fffde8" transparent opacity={0.12} />
      </mesh>

      <mesh>
        <sphereGeometry args={[0.18, 64, 64]} />
        <meshStandardMaterial
          map={moonTexture}
          roughness={1}
          metalness={0}
          emissive="#fffde8"
          emissiveIntensity={0.15}
        />
      </mesh>
    </group>
  );
}

type BirdSpec = {
  id: number;
  size: number;
  speed: number;
  flapSpeed: number;
  offset: number;
  x: number;
  y: number;
  z: number;
};

function Bird({ spec }: { spec: BirdSpec }) {
  const groupRef = useRef<THREE.Group>(null);
  const leftWingRef = useRef<THREE.Mesh>(null);
  const rightWingRef = useRef<THREE.Mesh>(null);

  const bodyGeometry = useMemo(() => {
    const shape = new THREE.Shape();
    const s = spec.size;

    shape.moveTo(-s * 0.6, 0);
    shape.quadraticCurveTo(-s * 0.3, s * 0.08, 0, s * 0.1);
    shape.quadraticCurveTo(s * 0.3, s * 0.12, s * 0.5, s * 0.05);
    shape.lineTo(s * 0.7, s * 0.02);
    shape.lineTo(s * 0.85, 0);
    shape.lineTo(s * 0.7, -s * 0.02);
    shape.quadraticCurveTo(s * 0.3, -s * 0.08, 0, -s * 0.06);
    shape.quadraticCurveTo(-s * 0.3, -s * 0.04, -s * 0.6, 0);

    const geo = new THREE.ShapeGeometry(shape);
    geo.rotateX(Math.PI / 2);
    return geo;
  }, [spec.size]);

  const wingGeometry = useMemo(() => {
    const shape = new THREE.Shape();
    const s = spec.size;

    shape.moveTo(0, 0);
    shape.lineTo(s * 0.1, s * 0.6);
    shape.quadraticCurveTo(s * 0.05, s * 0.7, -s * 0.1, s * 0.65);
    shape.lineTo(-s * 0.15, s * 0.4);
    shape.lineTo(-s * 0.1, 0);

    const geo = new THREE.ShapeGeometry(shape);
    return geo;
  }, [spec.size]);

  useFrame((state) => {
    if (!groupRef.current || !leftWingRef.current || !rightWingRef.current) return;
    const t = state.clock.getElapsedTime();

    groupRef.current.position.x += spec.speed * 0.008;

    groupRef.current.position.y = spec.y + Math.sin(t * 1.5 + spec.offset) * 0.015;

    if (groupRef.current.position.x > 6) {
      groupRef.current.position.x = -6;
    }

    const flapAngle = Math.sin(t * spec.flapSpeed + spec.offset) * 0.6;
    leftWingRef.current.rotation.x = flapAngle;
    rightWingRef.current.rotation.x = -flapAngle;
  });

  return (
    <group ref={groupRef} position={[spec.x, spec.y, spec.z]}>
      <mesh geometry={bodyGeometry}>
        <meshBasicMaterial color="#1a1a2e" side={THREE.DoubleSide} />
      </mesh>

      <mesh ref={leftWingRef} geometry={wingGeometry} position={[0, 0, spec.size * 0.02]}>
        <meshBasicMaterial color="#1a1a2e" side={THREE.DoubleSide} />
      </mesh>

      <mesh ref={rightWingRef} geometry={wingGeometry} position={[0, 0, -spec.size * 0.02]} rotation={[0, Math.PI, 0]}>
        <meshBasicMaterial color="#1a1a2e" side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

function Birds() {
  const birds = useMemo<BirdSpec[]>(
    () =>
      Array.from({ length: 8 }).map((_, index) => ({
        id: index,
        size: 0.06 + Math.random() * 0.04,
        speed: 0.12 + Math.random() * 0.15,
        flapSpeed: 8 + Math.random() * 4,
        offset: Math.random() * Math.PI * 2,
        x: -5 + Math.random() * 10,
        y: 0.8 + Math.random() * 1.2,
        z: -2 - Math.random() * 3,
      })),
    [],
  );

  return (
    <group>
      {birds.map((spec) => (
        <Bird key={spec.id} spec={spec} />
      ))}
    </group>
  );
}

export default function Hero3D() {
  if (typeof window === 'undefined' || !(window as typeof window & { ResizeObserver?: unknown }).ResizeObserver) {
    return null;
  }
  return (
    <div className="absolute inset-0">
      <Canvas camera={{ position: [0, 0, 6], fov: 40 }} dpr={[1, 2]} gl={{ antialias: true }}>
        <ambientLight intensity={0.3} />
        <directionalLight position={[5, 5, 5]} intensity={0.4} />
        <Starfield />
        <Moon />
        <Birds />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.15} />
      </Canvas>
    </div>
  );
}

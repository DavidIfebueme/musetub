import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import { BufferGeometry, Float32BufferAttribute, Group, LineSegments, Vector3 } from 'three';

function Moon() {
  const group = useRef<Group>(null);
  const color = useMemo(() => '#e2e8f0', []);

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.getElapsedTime();
    group.current.rotation.y = t * 0.03;
    group.current.rotation.x = t * 0.02;
  });

  return (
    <group ref={group} position={new Vector3(2.5, 1.6, -1)}>
      <mesh>
        <sphereGeometry args={[0.6, 48, 48]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <mesh position={new Vector3(0.15, 0.1, 0.2)}>
        <sphereGeometry args={[0.12, 24, 24]} />
        <meshBasicMaterial color="#cbd5f5" />
      </mesh>
      <mesh position={new Vector3(-0.2, -0.15, 0.18)}>
        <sphereGeometry args={[0.08, 24, 24]} />
        <meshBasicMaterial color="#cbd5f5" />
      </mesh>
    </group>
  );
}

type BirdSpec = {
  id: number;
  size: number;
  speed: number;
  offset: number;
  x: number;
  y: number;
  z: number;
  rotation: number;
};

function Bird({ spec }: { spec: BirdSpec }) {
  const lineRef = useRef<LineSegments>(null);
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    const wing = spec.size * 0.6;
    const vertices = new Float32Array([
      0, 0, 0,
      -wing, spec.size, 0,
      0, 0, 0,
      wing, spec.size, 0,
    ]);
    geo.setAttribute('position', new Float32BufferAttribute(vertices, 3));
    return geo;
  }, [spec.size]);

  useFrame((state) => {
    if (!lineRef.current) return;
    const t = state.clock.getElapsedTime();
    lineRef.current.position.x += spec.speed * 0.01;
    lineRef.current.position.y += Math.sin(t * 2 + spec.offset) * 0.001;
    if (lineRef.current.position.x > 5) {
      lineRef.current.position.x = -5;
    }
  });

  return (
    <lineSegments ref={lineRef} position={[spec.x, spec.y, spec.z]} rotation={[0, 0, spec.rotation]}>
      <primitive object={geometry} attach="geometry" />
      <lineBasicMaterial color="#e2e8f0" transparent opacity={0.8} />
    </lineSegments>
  );
}

function Birds() {
  const birds = useMemo<BirdSpec[]>(
    () =>
      Array.from({ length: 12 }).map((_, index) => ({
        id: index,
        size: 0.08 + Math.random() * 0.08,
        speed: 0.1 + Math.random() * 0.2,
        offset: Math.random() * Math.PI * 2,
        x: -4 + Math.random() * 8,
        y: -0.5 + Math.random() * 2,
        z: -1 - Math.random() * 2,
        rotation: Math.random() * Math.PI,
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
      <Canvas camera={{ position: [0, 0, 6], fov: 40 }} dpr={[1, 1.5]} gl={{ antialias: true }}>
        <ambientLight intensity={0.4} />
        <Stars radius={40} depth={25} count={1400} factor={1.4} fade speed={0.4} />
        <Moon />
        <Birds />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.25} />
      </Canvas>
    </div>
  );
}

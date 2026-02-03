import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Icosahedron, MeshDistortMaterial, OrbitControls, Stars } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import { Group } from 'three';

function Orb() {
  const group = useRef<Group>(null);
  const color = useMemo(() => '#e2e8f0', []);

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.getElapsedTime();
    group.current.rotation.y = t * 0.25;
    group.current.rotation.x = t * 0.15;
  });

  return (
    <group ref={group}>
      <Float speed={1.2} rotationIntensity={0.6} floatIntensity={0.8}>
        <Icosahedron args={[1.5, 2]}>
          <MeshDistortMaterial
            color={color}
            roughness={0.15}
            metalness={0.7}
            distort={0.35}
            speed={2.2}
          />
        </Icosahedron>
      </Float>
    </group>
  );
}

export default function Hero3D() {
  if (typeof window === 'undefined' || !(window as typeof window & { ResizeObserver?: unknown }).ResizeObserver) {
    return null;
  }
  return (
    <div className="absolute inset-0">
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[4, 4, 4]} intensity={1.2} />
        <Stars radius={40} depth={20} count={1200} factor={2} fade speed={1} />
        <Orb />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.6} />
      </Canvas>
    </div>
  );
}

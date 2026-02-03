import { Canvas, useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial, OrbitControls, Sphere, Stars } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import { Group } from 'three';

function Orb() {
  const group = useRef<Group>(null);
  const color = useMemo(() => '#e2e8f0', []);

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.getElapsedTime();
    group.current.rotation.y = t * 0.12;
    group.current.rotation.x = t * 0.08;
  });

  return (
    <group ref={group}>
      <Float speed={0.8} rotationIntensity={0.4} floatIntensity={0.5}>
        <Sphere args={[1.7, 96, 96]}>
          <MeshDistortMaterial
            color={color}
            roughness={0.2}
            metalness={0.6}
            distort={0.12}
            speed={0.6}
          />
        </Sphere>
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
      <Canvas camera={{ position: [0, 0, 6], fov: 40 }} dpr={[1, 1.5]} gl={{ antialias: true }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[3, 5, 4]} intensity={1} />
        <Stars radius={30} depth={20} count={600} factor={1} fade speed={0.3} />
        <Orb />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.25} />
      </Canvas>
    </div>
  );
}

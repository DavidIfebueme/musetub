import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import { BufferGeometry, Float32BufferAttribute, Group, Mesh, MeshBasicMaterial, Vector3 } from 'three';

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

function Birds() {
  const group = useRef<Group>(null);
  const birds = useMemo(() => {
    return Array.from({ length: 12 }).map((_, index) => {
      const geometry = new BufferGeometry();
      const size = 0.08 + Math.random() * 0.08;
      const wing = size * 0.6;
      const vertices = new Float32Array([
        0, 0, 0,
        -wing, size, 0,
        wing, size, 0,
      ]);
      geometry.setAttribute('position', new Float32BufferAttribute(vertices, 3));
      const material = new MeshBasicMaterial({ color: '#e2e8f0' });
      const mesh = new Mesh(geometry, material);
      mesh.position.set(-4 + Math.random() * 8, -0.5 + Math.random() * 2, -1 - Math.random() * 2);
      mesh.rotation.z = Math.random() * Math.PI;
      mesh.userData = { speed: 0.1 + Math.random() * 0.2, offset: Math.random() * Math.PI * 2 };
      return mesh;
    });
  }, []);

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.getElapsedTime();
    group.current.children.forEach((child) => {
      const speed = child.userData.speed as number;
      const offset = child.userData.offset as number;
      child.position.x += speed * 0.01;
      child.position.y += Math.sin(t * 2 + offset) * 0.001;
      if (child.position.x > 5) {
        child.position.x = -5;
      }
    });
  });

  return <group ref={group}>{birds.map((mesh) => mesh)}</group>;
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

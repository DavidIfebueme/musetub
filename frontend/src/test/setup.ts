import '@testing-library/jest-dom/vitest';

const store = new Map<string, string>();

const localStorageMock = {
	getItem: (key: string) => {
		return store.has(key) ? store.get(key)! : null;
	},
	setItem: (key: string, value: string) => {
		store.set(key, String(value));
	},
	removeItem: (key: string) => {
		store.delete(key);
	},
	clear: () => {
		store.clear();
	},
};

Object.defineProperty(globalThis, 'localStorage', {
	value: localStorageMock,
	configurable: true,
});

Object.defineProperty(globalThis, 'sessionStorage', {
	value: localStorageMock,
	configurable: true,
});

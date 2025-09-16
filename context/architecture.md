# Frontend Architecture & Best Practices

This document defines the coding standards, file organization, and architectural patterns for the Zalanko fashion e-commerce frontend application.

## 📁 File Structure

### Root Structure
```
app/frontend/src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI primitives (buttons, cards, etc.)
│   └── layout/         # Layout-specific components
├── features/           # Feature-specific components (future)
├── hooks/              # Custom React hooks
├── utils/              # Pure utility functions
├── constants/          # Application constants
├── types/              # TypeScript type definitions
├── lib/                # Third-party library configurations
└── App.tsx             # Main application component
```

## 🧩 Component Organization

### Component Types

1. **UI Components** (`components/ui/`)
   - Pure, reusable components
   - No business logic
   - Examples: `button.tsx`, `card.tsx`, `status-message.tsx`

2. **Layout Components** (`components/layout/`)
   - Structure and positioning components
   - Examples: `Header.tsx`, `Sidebar.tsx`, `Footer.tsx`

3. **Feature Components** (`features/`)
   - Domain-specific components
   - Can contain business logic
   - Examples: `products/`, `cart/`, `authentication/`

### Component Best Practices

#### Naming Conventions
- **Files**: PascalCase with `.tsx` extension (e.g., `ProductCard.tsx`)
- **Components**: Match filename (e.g., `function ProductCard()`)
- **Props Interfaces**: Add `Props` suffix (e.g., `ProductCardProps`)

#### Component Structure
```tsx
// 1. Imports - External libraries first, then internal
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { getColorHex } from "@/utils/colors";

// 2. Types/Interfaces
interface ProductCardProps {
  product: Product;
  onSelect?: (id: string) => void;
}

// 3. Component Definition
export default function ProductCard({ product, onSelect }: ProductCardProps) {
  // 4. Hooks and state
  const [isHovered, setIsHovered] = useState(false);
  
  // 5. Derived state and computations
  const isOnSale = product.salePrice < product.price;
  
  // 6. Event handlers
  const handleClick = () => {
    onSelect?.(product.id);
  };
  
  // 7. JSX return
  return (
    <Card onClick={handleClick}>
      {/* Component content */}
    </Card>
  );
}
```

## 🔧 Utilities Organization

### Utils Directory (`utils/`)
- **Single Responsibility**: Each file handles one domain
- **Pure Functions**: No side effects
- **Well Documented**: JSDoc comments for all functions

#### Examples:
```typescript
// utils/colors.ts - Color-related utilities
export const getColorHex = (colorName: string): string => { ... }

// utils/pricing.ts - Price calculation utilities  
export const calculatePricing = (price: number, salePrice?: number): PricingInfo => { ... }

// utils/formatting.ts - Text/number formatting
export const formatCurrency = (amount: number): string => { ... }
```

### Constants Directory (`constants/`)
- **Grouped by Domain**: Related constants together
- **UPPER_SNAKE_CASE**: For primitive constants
- **Objects**: For complex mappings

#### Examples:
```typescript
// constants/colors.ts
export const COLOR_MAP = {
  white: '#FFFFFF',
  black: '#000000',
  // ...
} as const;

// constants/navigation.ts
export const PAGE_TYPES = ['main', 'favorites', 'cart', 'messages'] as const;
export type PageType = typeof PAGE_TYPES[number];
```

## 🪝 Custom Hooks

### Hook Best Practices
- **Prefix with `use`**: Follow React conventions
- **Single Responsibility**: One concern per hook
- **Return Objects**: For multiple values, use objects with named properties

#### Examples:
```typescript
// hooks/useCart.ts
export function useCart() {
  const [items, setItems] = useState<CartItem[]>([]);
  
  const addItem = useCallback((item: CartItem) => {
    setItems(prev => [...prev, item]);
  }, []);
  
  return {
    items,
    addItem,
    removeItem,
    total: calculateTotal(items)
  };
}

// hooks/useLocalStorage.ts
export function useLocalStorage<T>(key: string, defaultValue: T) {
  // Implementation
  return [value, setValue] as const;
}
```

## 🎨 Styling Guidelines

### Tailwind CSS Best Practices
- **Utility-First**: Use Tailwind classes directly
- **Component Extraction**: Extract repeated patterns to components
- **Responsive Design**: Mobile-first approach
- **Dark Theme**: Use dark mode variants consistently

#### Color System
```tsx
// Use semantic color names from our palette
className="bg-gray-800 text-white border-gray-700"

// For interactive elements
className="hover:bg-purple-600 active:bg-purple-700"

// For brand colors
className="bg-gradient-to-r from-purple-600 to-pink-600"
```

## 🔄 State Management

### Local State (useState)
- Use for component-specific state
- Keep state as close to where it's used as possible

### Lifting State Up
- When multiple components need the same state
- Lift to the lowest common ancestor

### Future: Context/Zustand
- For truly global state (user auth, app theme)
- Avoid prop drilling for deeply nested components

## 📝 TypeScript Best Practices

### Type Definitions
- **Interfaces over Types**: For object shapes
- **Union Types**: For string literals and enums
- **Generic Constraints**: When creating reusable components

#### Examples:
```typescript
// Good: Specific union types
type PageType = 'main' | 'favorites' | 'cart' | 'messages';

// Good: Interface for object shapes
interface Product {
  id: string;
  title: string;
  price: number;
  salePrice?: number;
}

// Good: Generic with constraints
interface ListProps<T extends { id: string }> {
  items: T[];
  onSelect: (item: T) => void;
}
```

## 🧪 Testing Strategy (Future)

### Testing Pyramid
1. **Unit Tests**: Utils, hooks, pure functions
2. **Component Tests**: Individual component behavior
3. **Integration Tests**: Feature workflows
4. **E2E Tests**: Critical user journeys

## 📦 Import/Export Patterns

### Import Order
```typescript
// 1. React and external libraries
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

// 2. Internal utilities and constants
import { getColorHex } from '@/utils/colors';
import { BRAND_COLORS } from '@/constants/colors';

// 3. Components (UI first, then feature-specific)
import { Card } from '@/components/ui/card';
import { ProductImage } from '@/features/products/ProductImage';

// 4. Types
import type { Product } from '@/types/product';
```

### Export Patterns
```typescript
// Prefer default exports for components
export default function ProductCard() { ... }

// Named exports for utilities
export const formatPrice = (price: number) => { ... };
export const calculateDiscount = (original: number, sale: number) => { ... };
```

## 🚀 Performance Guidelines

### Component Optimization
- **React.memo**: For expensive components that re-render frequently
- **useCallback**: For functions passed to child components
- **useMemo**: For expensive calculations

### Bundle Optimization
- **Lazy Loading**: Use `React.lazy` for route-level code splitting
- **Tree Shaking**: Ensure imports are specific (named imports)
- **Asset Optimization**: Optimize images and use appropriate formats

## 🔧 Development Workflow

### Before Adding New Features
1. **Check existing patterns**: Follow established conventions
2. **Consider reusability**: Can this be generalized?
3. **Update documentation**: Keep this guide current
4. **Test thoroughly**: Ensure no regressions

### Code Review Checklist
- [ ] Follows naming conventions
- [ ] Proper file organization
- [ ] TypeScript types are correct
- [ ] No duplicate code
- [ ] Performance considerations addressed
- [ ] Accessibility guidelines followed

## 📋 Quick Reference

### When to Create New Files
- **New Component**: Always in appropriate directory
- **New Utility**: If it's domain-specific and reusable
- **New Hook**: If state logic is reused across components
- **New Constant**: If values are used in multiple places

### File Naming Quick Guide
- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Constants: `camelCase.ts`
- Hooks: `useCamelCase.ts`
- Types: `camelCase.ts`

---

**Remember**: Consistency is key. When in doubt, follow existing patterns in the codebase.
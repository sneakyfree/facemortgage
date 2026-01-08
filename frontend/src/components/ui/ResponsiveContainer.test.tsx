/**
 * ResponsiveContainer component tests.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  ResponsiveContainer,
  ResponsiveGrid,
  Stack,
  HideOnMobile,
  ShowOnMobile,
} from './ResponsiveContainer';

describe('ResponsiveContainer', () => {
  it('renders children', () => {
    render(<ResponsiveContainer>Test content</ResponsiveContainer>);

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('applies base responsive classes', () => {
    const { container } = render(
      <ResponsiveContainer>Content</ResponsiveContainer>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('w-full');
    expect(div).toHaveClass('max-w-7xl');
    expect(div).toHaveClass('mx-auto');
    expect(div).toHaveClass('px-4');
  });

  it('applies custom className', () => {
    const { container } = render(
      <ResponsiveContainer className="custom-class">Content</ResponsiveContainer>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('custom-class');
  });

  it('applies mobile nav padding when withMobileNav is true', () => {
    const { container } = render(
      <ResponsiveContainer withMobileNav>Content</ResponsiveContainer>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('pt-20');
    expect(div).toHaveClass('pb-20');
  });

  it('does not apply mobile nav padding by default', () => {
    const { container } = render(
      <ResponsiveContainer>Content</ResponsiveContainer>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).not.toHaveClass('pt-20');
    expect(div).not.toHaveClass('pb-20');
  });
});

describe('ResponsiveGrid', () => {
  it('renders children', () => {
    render(
      <ResponsiveGrid>
        <div>Item 1</div>
        <div>Item 2</div>
      </ResponsiveGrid>
    );

    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('applies grid class', () => {
    const { container } = render(
      <ResponsiveGrid>
        <div>Item</div>
      </ResponsiveGrid>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('grid');
  });

  it('applies medium gap by default', () => {
    const { container } = render(
      <ResponsiveGrid>
        <div>Item</div>
      </ResponsiveGrid>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-4');
  });

  it('applies small gap when specified', () => {
    const { container } = render(
      <ResponsiveGrid gap="sm">
        <div>Item</div>
      </ResponsiveGrid>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-3');
  });

  it('applies large gap when specified', () => {
    const { container } = render(
      <ResponsiveGrid gap="lg">
        <div>Item</div>
      </ResponsiveGrid>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-6');
  });

  it('applies custom className', () => {
    const { container } = render(
      <ResponsiveGrid className="my-grid">
        <div>Item</div>
      </ResponsiveGrid>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('my-grid');
  });

  it('sets grid template with default minColWidth', () => {
    const { container } = render(
      <ResponsiveGrid>
        <div>Item</div>
      </ResponsiveGrid>
    );

    const div = container.firstChild as HTMLElement;
    expect(div.style.gridTemplateColumns).toContain('280px');
  });

  it('sets grid template with custom minColWidth', () => {
    const { container } = render(
      <ResponsiveGrid minColWidth={350}>
        <div>Item</div>
      </ResponsiveGrid>
    );

    const div = container.firstChild as HTMLElement;
    expect(div.style.gridTemplateColumns).toContain('350px');
  });
});

describe('Stack', () => {
  it('renders children', () => {
    render(
      <Stack>
        <div>Child 1</div>
        <div>Child 2</div>
      </Stack>
    );

    expect(screen.getByText('Child 1')).toBeInTheDocument();
    expect(screen.getByText('Child 2')).toBeInTheDocument();
  });

  it('applies vertical direction by default', () => {
    const { container } = render(
      <Stack>
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('flex');
    expect(div).toHaveClass('flex-col');
  });

  it('applies horizontal direction when specified', () => {
    const { container } = render(
      <Stack direction="horizontal">
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('flex');
    expect(div).toHaveClass('flex-row');
  });

  it('applies responsive direction when specified', () => {
    const { container } = render(
      <Stack direction="responsive">
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('flex');
    expect(div).toHaveClass('flex-col');
    expect(div).toHaveClass('sm:flex-row');
  });

  it('applies medium gap by default', () => {
    const { container } = render(
      <Stack>
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-4');
  });

  it('applies extra small gap when specified', () => {
    const { container } = render(
      <Stack gap="xs">
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-1');
  });

  it('applies small gap when specified', () => {
    const { container } = render(
      <Stack gap="sm">
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-2');
  });

  it('applies large gap when specified', () => {
    const { container } = render(
      <Stack gap="lg">
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-6');
  });

  it('applies extra large gap when specified', () => {
    const { container } = render(
      <Stack gap="xl">
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('gap-8');
  });

  it('applies custom className', () => {
    const { container } = render(
      <Stack className="custom-stack">
        <div>Child</div>
      </Stack>
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('custom-stack');
  });
});

describe('HideOnMobile', () => {
  it('renders children', () => {
    render(<HideOnMobile>Hidden on mobile</HideOnMobile>);

    expect(screen.getByText('Hidden on mobile')).toBeInTheDocument();
  });

  it('applies md:block hidden classes by default', () => {
    const { container } = render(<HideOnMobile>Content</HideOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('hidden');
    expect(div).toHaveClass('md:block');
  });

  it('applies sm:block hidden classes when showAt is sm', () => {
    const { container } = render(<HideOnMobile showAt="sm">Content</HideOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('hidden');
    expect(div).toHaveClass('sm:block');
  });

  it('applies lg:block hidden classes when showAt is lg', () => {
    const { container } = render(<HideOnMobile showAt="lg">Content</HideOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('hidden');
    expect(div).toHaveClass('lg:block');
  });

  it('applies xl:block hidden classes when showAt is xl', () => {
    const { container } = render(<HideOnMobile showAt="xl">Content</HideOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('hidden');
    expect(div).toHaveClass('xl:block');
  });
});

describe('ShowOnMobile', () => {
  it('renders children', () => {
    render(<ShowOnMobile>Visible on mobile</ShowOnMobile>);

    expect(screen.getByText('Visible on mobile')).toBeInTheDocument();
  });

  it('applies md:hidden class by default', () => {
    const { container } = render(<ShowOnMobile>Content</ShowOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('md:hidden');
  });

  it('applies sm:hidden class when hideAt is sm', () => {
    const { container } = render(<ShowOnMobile hideAt="sm">Content</ShowOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('sm:hidden');
  });

  it('applies lg:hidden class when hideAt is lg', () => {
    const { container } = render(<ShowOnMobile hideAt="lg">Content</ShowOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('lg:hidden');
  });

  it('applies xl:hidden class when hideAt is xl', () => {
    const { container } = render(<ShowOnMobile hideAt="xl">Content</ShowOnMobile>);

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('xl:hidden');
  });
});

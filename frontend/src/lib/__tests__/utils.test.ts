import { cn } from '@/lib/utils';

describe('cn utility', () => {
  it('joins class names with spaces', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c');
  });

  it('filters out falsy values', () => {
    expect(cn('a', false && 'b', 'c')).toBe('a c');
    expect(cn('a', null, 'c')).toBe('a c');
    expect(cn('a', undefined, 'c')).toBe('a c');
    expect(cn('a', 0, 'c')).toBe('a c');
    expect(cn('a', '', 'c')).toBe('a c');
  });

  it('handles empty input', () => {
    expect(cn()).toBe('');
  });

  it('handles single class', () => {
    expect(cn('single')).toBe('single');
  });
});
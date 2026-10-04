import { render, screen, fireEvent } from '@testing-library/react';
import { TaskCard } from '@/components/TaskCard';
import { vi, describe, it, expect, beforeEach } from 'vitest';

describe('TaskCard', () => {
  const mockTask = {
    id: 'task-1',
    title: 'Test Task',
    description: 'Test description',
    status: 'open',
    source_type: 'manual',
    due_date: '2026-12-31',
    owner_id: 'user-1',
    exception_id: 'exc-1',
  };

  const mockOnStatusChange = vi.fn();
  const mockOnDraft = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders task title and description', () => {
    render(<TaskCard task={mockTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('renders source type', () => {
    render(<TaskCard task={mockTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    // The component renders "manual" (lowercase) not "MANUAL"
    expect(screen.getByText('manual')).toBeInTheDocument();
  });

  it('renders due date', () => {
    render(<TaskCard task={mockTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    // Date format is DD/MM/YYYY in the component
    expect(screen.getByText('31/12/2026')).toBeInTheDocument();
  });

  it('renders owner', () => {
    render(<TaskCard task={mockTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    // Owner ID with prefix removed
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('calls onStatusChange when status is changed via dropdown', () => {
    render(<TaskCard task={mockTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    // Click the dropdown button
    const dropdownButton = screen.getByRole('button', { name: /task options/i });
    fireEvent.click(dropdownButton);
    
    // Click "Move to In Progress"
    const moveToInProgress = screen.getByText('Move to In Progress');
    fireEvent.click(moveToInProgress);
    
    expect(mockOnStatusChange).toHaveBeenCalledWith('task-1', 'in_progress');
  });

  it('calls onDraft when "Draft Follow-up" is clicked', () => {
    render(<TaskCard task={mockTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    // Click the dropdown button
    const dropdownButton = screen.getByRole('button', { name: /task options/i });
    fireEvent.click(dropdownButton);
    
    // Click "Draft Follow-up"
    const draftFollowup = screen.getByText('Draft Follow-up');
    fireEvent.click(draftFollowup);
    
    expect(mockOnDraft).toHaveBeenCalledWith(mockTask);
  });

  it('shows overdue indicator for past due dates', () => {
    const overdueTask = { ...mockTask, due_date: '2020-01-01' };
    render(<TaskCard task={overdueTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    // The overdue indicator shows an AlertTriangle SVG with data-testid="alerttriangle"
    expect(screen.getByTestId('alerttriangle')).toBeInTheDocument();
  });

  it('does not show overdue indicator for future due dates', () => {
    const futureTask = { ...mockTask, due_date: '2030-01-01' };
    render(<TaskCard task={futureTask} onStatusChange={mockOnStatusChange} onDraft={mockOnDraft} />);
    
    const alertTriangle = screen.queryByTestId('alert-triangle');
    expect(alertTriangle).not.toBeInTheDocument();
  });
});
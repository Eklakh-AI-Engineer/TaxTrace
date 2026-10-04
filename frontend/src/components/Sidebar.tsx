'use client';

import Link from 'next/link';
import { Home, FileText, AlertTriangle, FileWarning, CheckSquare, Search, Shield, Settings, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePathname } from 'next/navigation';

const navItems = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Clients', href: '/clients', icon: Search },
  { name: 'Reconciliation', href: '/reconciliation', icon: FileText },
  { name: 'Exceptions', href: '/exceptions', icon: AlertTriangle },
  { name: 'Notices', href: '/notices', icon: FileWarning },
  { name: 'Tasks', href: '/tasks', icon: CheckSquare },
  { name: 'Knowledge', href: '/knowledge', icon: Shield },
  { name: 'Chat Simulator', href: '/chat', icon: MessageCircle },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col bg-slate-900 text-white">
      <div className="flex h-16 items-center px-6">
        <h1 className="text-xl font-bold tracking-tight text-white">TaxTrace</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
                'group flex items-center rounded-md px-3 py-2 text-sm font-medium'
              )}
            >
              <item.icon
                className={cn(
                  isActive ? 'text-indigo-400' : 'text-slate-400 group-hover:text-white',
                  'mr-3 h-5 w-5 flex-shrink-0'
                )}
                aria-hidden="true"
              />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

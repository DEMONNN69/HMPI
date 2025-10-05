import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/lib/auth-context';
import { 
  Home, 
  Calculator, 
  Upload, 
  Map, 
  Database,
  LogOut,
  BarChart3
} from 'lucide-react';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();

  const navigationItems = [
    {
      label: 'Dashboard',
      path: '/',
      icon: Home,
      description: 'Water quality overview'
    },
    {
      label: 'HMPI Calculator',
      path: '/hmpi-calculations',
      icon: Calculator,
      description: 'Calculate HMPI indices'
    },
    {
      label: 'Import Data',
      path: '/ground-water-samples',
      icon: Upload,
      description: 'Manage ground water samples'
    },
    {
      label: 'Interactive Map',
      path: '/map',
      icon: Map,
      description: 'Visualize water quality data'
    }
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 mr-4">
              <BarChart3 className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold">AquaGuard Monitor</span>
            </div>
            
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              
              return (
                <Button
                  key={item.path}
                  variant={active ? "default" : "ghost"}
                  size="sm"
                  onClick={() => navigate(item.path)}
                  className="flex items-center gap-2 relative"
                  title={item.description}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                  {active && (
                    <Badge variant="secondary" className="ml-1 text-xs">
                      Active
                    </Badge>
                  )}
                </Button>
              );
            })}
          </div>

          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => logout()}
            className="flex items-center gap-2"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default Navigation;
import { Dashboard } from "@/components/Dashboard";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

const Index = () => {
  const { logout } = useAuth();
  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-end">
        <Button variant="outline" onClick={() => logout()}>Logout</Button>
      </div>
      <Dashboard />
    </div>
  );
};

export default Index;

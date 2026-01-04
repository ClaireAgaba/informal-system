import { useNavigate } from 'react-router-dom';
import { Users, UserPlus, Building2 } from 'lucide-react';
import Card from '@shared/components/Card';

const UsersIndex = () => {
  const navigate = useNavigate();

  const userCategories = [
    {
      title: 'Staff Members',
      description: 'UVTAB staff members with full system access',
      icon: Users,
      path: '/users/staff',
      color: 'primary',
    },
    {
      title: 'Support Staff',
      description: 'Non-staff members like interns with limited access',
      icon: UserPlus,
      path: '/users/support-staff',
      color: 'blue',
    },
    {
      title: 'Center Representatives',
      description: 'Assessment center representatives with center-specific access',
      icon: Building2,
      path: '/users/center-representatives',
      color: 'green',
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="text-gray-600 mt-1">Manage staff and support staff members</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {userCategories.map((category) => {
          const Icon = category.icon;
          return (
            <Card
              key={category.path}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => navigate(category.path)}
            >
              <Card.Content className="p-6">
                <div className="flex items-start space-x-4">
                  <div className={`p-3 rounded-lg bg-${category.color}-100`}>
                    <Icon className={`w-8 h-8 text-${category.color}-600`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {category.title}
                    </h3>
                    <p className="text-sm text-gray-600">{category.description}</p>
                  </div>
                </div>
              </Card.Content>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default UsersIndex;

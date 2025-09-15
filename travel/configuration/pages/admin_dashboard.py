import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_dashboard import admin_dashboard

if __name__ == "__main__":
    admin_dashboard()

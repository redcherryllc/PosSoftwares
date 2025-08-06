const sidebar = document.getElementById('sidebar');
        const toggleButton = document.getElementById('toggle-sidebar');
        const menuItems = document.querySelectorAll('.sidebar-menu .menu-item');

 
        const isMobile = window.innerWidth <= 991;

        if (isMobile) {
            
            sidebar.classList.add('collapsed');
            sidebar.classList.remove('expanded');
            localStorage.setItem('sidebarState', 'collapsed');
        } else {
          
            const savedState = localStorage.getItem('sidebarState');
            if (savedState === 'expanded') {
                sidebar.classList.remove('collapsed');
                sidebar.classList.add('expanded');
            } else {
                sidebar.classList.add('collapsed');
                sidebar.classList.remove('expanded');
            }
        }

       
        toggleButton.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            sidebar.classList.toggle('expanded');
            localStorage.setItem('sidebarState', sidebar.classList.contains('collapsed') ? 'collapsed' : 'expanded');
        });

     
        menuItems.forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth <= 991) {
                    sidebar.classList.add('collapsed');
                    sidebar.classList.remove('expanded');
                    localStorage.setItem('sidebarState', 'collapsed');
                }
            });
        });

     
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const isNowMobile = window.innerWidth <= 991;
                const savedState = localStorage.getItem('sidebarState');

                if (isNowMobile) {
                    
                    sidebar.classList.add('collapsed');
                    sidebar.classList.remove('expanded');
                    localStorage.setItem('sidebarState', 'collapsed');
                } else if (savedState === 'expanded') {
                   
                    sidebar.classList.remove('collapsed');
                    sidebar.classList.add('expanded');
                }
            }, 100);
        });
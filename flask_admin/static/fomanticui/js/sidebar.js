(function () {
  const sidebarMenu = document.getElementById('sidebar-menu');
  const sidebarToggler = document.getElementById('sidebar-menu-toggler');
  const mainPusher = document.getElementById('main-pusher');

  // Abort early if the expected elements do not exist
  if (!sidebarMenu || !sidebarToggler || !mainPusher) {
    console.warn('Sidebar elements not found - sidebar script disabled.');
    return;
  }

  // shouldOpenSidebar is set by preload script on window
  if (window.shouldOpenSidebar) {
    setSidebarState(true);
    document.documentElement.classList.remove('sidebar-pref-open');
  }

  // Helper to set sidebar state
  function setSidebarState(isOpen) {
    sidebarToggler.setAttribute('aria-expanded', isOpen);
    if (isOpen) {
      sidebarMenu.classList.add('open');
      mainPusher.classList.add('sidebar-open');
    } else {
      sidebarMenu.classList.remove('open');
      mainPusher.classList.remove('sidebar-open');
    }
  }

  sidebarToggler.addEventListener('click', () => {
    const isOpen = !sidebarMenu.classList.contains('open');
    setSidebarState(isOpen);
    const isMobile = () => window.matchMedia && window.matchMedia('(max-width: 768px)').matches;
    if (!isMobile()) {
      try {
        localStorage.setItem('sidebarPreference', isOpen ? '1' : '0');
      } catch (e) {
        /* storage disabled */
      }
    }
  });
})();

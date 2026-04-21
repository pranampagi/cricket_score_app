<template>
  <nav class="navbar">
    <div class="container nav-inner">
      <RouterLink to="/" class="nav-brand">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="24" height="24"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 7.07 17.07M12 2a10 10 0 0 0-7.07 17.07M8 12h8M12 8v8"/></svg>
        <span>CricScore</span>
      </RouterLink>

      <div class="nav-links hide-mobile">
        <RouterLink to="/" class="nav-link">Home</RouterLink>
        <RouterLink to="/match/new" class="nav-link">New Match</RouterLink>
        <RouterLink to="/tournaments" class="nav-link">Tournaments</RouterLink>
      </div>

      <RouterLink to="/match/new" class="btn btn-primary btn-sm hide-mobile">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
        New Match
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(10,15,26,0.92); backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
}
.nav-inner { display: flex; align-items: center; gap: 2rem; height: 60px; }
.nav-brand {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 1.15rem; font-weight: 800; color: var(--primary);
  flex-shrink: 0;
}
.nav-brand svg { color: var(--primary); }
.nav-links { display: flex; gap: 0.25rem; flex: 1; }
.nav-link {
  padding: 0.4rem 0.875rem; border-radius: var(--radius-sm);
  font-size: 0.875rem; font-weight: 500; color: var(--text-dim);
  transition: color var(--transition), background var(--transition);
}
.nav-link:hover, .nav-link.router-link-active { color: var(--primary); background: var(--primary-glow); }
</style>

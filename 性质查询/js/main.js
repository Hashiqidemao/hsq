// 入口脚本，负责导航和模块动态加载
document.addEventListener('DOMContentLoaded', () => {
  const navLinks = document.querySelectorAll('nav a[data-module]');
  const app = document.getElementById('app');

  // 默认加载第一个模块
  setActive(navLinks[0]);
  loadModule(navLinks[0].dataset.module);

  navLinks.forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      setActive(link);
      loadModule(link.dataset.module);
    });
  });

  function setActive(activeLink) {
    navLinks.forEach(l => l.classList.remove('active'));
    activeLink.classList.add('active');
  }

  async function loadModule(moduleName) {
    app.innerHTML = '<p>加载中...</p>';
    try {
      const module = await import(`./modules/${moduleName}.js`);
      app.innerHTML = '';
      if (module && typeof module.init === 'function') {
        module.init(app);
      } else {
        app.innerHTML = '<p>模块加载失败：init 方法未找到</p>';
      }
    } catch (err) {
      app.innerHTML = `<p>模块加载失败：${err.message}</p>`;
    }
  }
});

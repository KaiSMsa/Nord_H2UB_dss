<template>
  <footer class="app-footer">
    <span>
      © {{ year }} NTNU — {{ projectName }}
      &nbsp;|&nbsp;
      MIT License
      &nbsp;|&nbsp;
      Version {{ version }}
      &nbsp;|&nbsp;
      Last updated: {{ lastUpdate }}
    </span>
  </footer>
</template>

<script>
export default {
  name: "AppFooter",
  computed: {
    year() {
      return new Date().getFullYear();
    },
    projectName() {
      return "GREENPORT Decision Support System (DSS)";
    },
    version() {
      return "1.0.1"; // ← update when you release
    },
    lastUpdate() {
      return "Feb 2026"; // Update this manually when you update the app, or automate it with a build script if you like!
    },
  },
};
</script>

<style scoped>
.app-footer {
  flex-shrink: 0;
  padding: 14px 12px;
  text-align: center;
  font-size: 0.8rem;
  color: #666;
  background-color: #fafafa;
  border-top: 1px solid #e0e0e0;
}
</style>

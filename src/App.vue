<template>
  <div id="app">
    <md-toolbar>
      <h2 class="md-title">
        Monitorrent
        <span class="md-title-caption">v.1.1.2a</span>       
      </h2>
      <span style="flex: 1"></span>
      <md-button class="md-icon-button">
        <md-icon>settings</md-icon>
      </md-button>
      <md-button class="md-icon-button">
        <md-icon>exit_to_app</md-icon>
      </md-button>
    </md-toolbar>

    <div class="mt-content-view">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
export default {
  name: 'app'
}
</script>

<style>
.md-title-caption {
  font-size: 12px;
  letter-spacing: 0.020em;
}

.mt-content-view {
  margin: auto;
  width: 100%;
  max-width: 1200px;
  box-sizing: border-box;
}
</style>

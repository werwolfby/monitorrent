<template>
  <div>
    <md-layout md-row md-gutter="24" class="mt-topics-header">
      <md-layout md-flex>
        <md-input-container>
          <label>Filter</label>
          <md-input/>
        </md-input-container>
      </md-layout>

      <div>
        <md-input-container>
          <label>Sort</label>
          <md-select v-model="order">
            <md-option value="display_name">Name</md-option>
            <md-option value="-last_update">Last Update</md-option>
          </md-select>
        </md-input-container>
      </div>

      <md-button class="md-icon-button" style="margin: auto 12px">
        <md-icon>add</md-icon>
      </md-button>
    </md-layout>
    <md-divider></md-divider>
  </div>
</template>

<script>
export default {
  data: () => {
    return {
      order: '-last_update'
    }
  },
  name: 'TopicsHeader'
}
</script>

<style scoped>
.mt-topics-header {
  padding: 0px 16px;
}
</style>

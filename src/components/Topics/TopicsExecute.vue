<template>
  <div>
    <md-layout md-row md-gutter="24" class="mt-topics-header" v-if='loading'>
      <md-layout md-flex>
        <h4 md-flex class="mt-subheader mt-executing">
          <span class="mt-bold">Updating torrents...</span>
        </h4>
      </md-layout>
    </md-layout>
    <md-layout md-row md-gutter="24" class="mt-topics-header" v-else-if='!loading && !has_topics'>
      <md-layout md-flex>
        <h4 md-flex class="mt-subheader mt-executing">
          <span class="mt-bold">Add torrent and press execute</span>
        </h4>
      </md-layout>
    </md-layout>
    <md-layout md-row md-gutter="24" class="mt-topics-header" v-else>
      <md-layout md-flex>
        <h4 md-flex class="mt-subheader mt-executing">
          <span class="mt-bold">Last Executed</span>&nbsp;at {{execute.finish_time | formatDate('HH:mm')}} ({{relative_execute}})
        </h4>
      </md-layout>
      <md-button class="md-icon-button" style="margin: auto 12px">
        <md-icon>input</md-icon>
      </md-button>
    </md-layout>
    <md-divider></md-divider>
  </div>
</template>

<script>
export default {
  props: ['loading', 'has_topics'],
  data: function () {
    return {
      'execute': {
        'finish_time': new Date()
      },
      'relative_execute': '7 minutes ago'
    }
  },
  name: 'TopicsExecute'
}
</script>

<style scoped>
.mt-topics-header {
  padding: 0px 16px;
}

.mt-executing {
  text-overflow: ellipsis;
  overflow: hidden !important;
  white-space: nowrap;
}

.mt-bold {
  font-weight: 600;
}

.mt-subheader {
  font-size: 16px;
  font-weight: 400;
  letter-spacing: 0.010em;
  line-height: 24px;
}
</style>

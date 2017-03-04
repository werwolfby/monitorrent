<template>
    <md-dialog ref="addTopicDialog">
        <md-dialog-title>Add Topic</md-dialog-title>

        <md-dialog-content style="width: 500px">
            <md-layout md-gutter="24">
                <md-layout md-flex="100">
                    <md-input-container>
                        <label>URL</label>
                        <md-input v-model="topicUrl"></md-input>
                    </md-input-container>
                </md-layout>
            </md-layout>
            <md-progress md-indeterminate :style="{opacity: loading ? 1: 0}"></md-progress>
            <mt-dynamic-form :form="form"></mt-dynamic-form>
            <md-layout md-gutter="24">
                <md-layout md-flex="100">
                    <md-input-container :class="{'md-input-invalid': !loadingDownloadDir && !hasDownloadDir}">
                        <label>Download dir</label>
                        <md-input v-model="downloadDir" :disabled="loadingDownloadDir || !hasDownloadDir"></md-input>
                        <span v-if="!loadingDownloadDir && !hasDownloadDir" class="md-error" style="color: #ff5722">{{defaultClientName}} doesn't support download dir settings</span>
                    </md-input-container>
                </md-layout>
            </md-layout>
            <md-progress md-indeterminate :style="{opacity: loadingDownloadDir ? 1: 0}"></md-progress>
        </md-dialog-content>

        <md-dialog-actions>
            <md-button class="md-primary" ref="addTopicDialogCancel" @click.native="close">Cancel</md-button>
            <md-button class="md-primary md-accent" ref="add" :disabled="loading || loadingDownloadDir || !defaultClientName || !parsed">Add</md-button>
        </md-dialog-actions>
    </md-dialog>
</template>

<script>
import api from '../../api/monitorrent'
import DynamicForm from '../DynamicForm.jsx'

export default {
    data: () => ({
        topicUrl: '',
        downloadDir: '',
        hasDownloadDir: false,
        defaultClientName: '',
        form: {},
        parsed: false,
        loading: false,
        loadingDownloadDir: false
    }),
    watch: {
        topicUrl () {
            this.parseUrl()
        }
    },
    name: 'AddTopicDialog',
    components: {
        'mt-dynamic-form': DynamicForm
    },
    methods: {
        async parseUrl () {
            if (!this.topicUrl) {
                this.form = {rows: []}
                return
            }

            try {
                this.loading = true
                this.parsed = false
                const parseResult = await api.parseUrl(this.topicUrl)
                this.form = {rows: parseResult.form, model: parseResult.settings}
                this.parsed = true
            } catch (err) {
                this.form = {rows: []}
                console.log(err)
            } finally {
                this.loading = false
            }
        },
        async defaultClient () {
            try {
                this.downloadDir = ''
                this.hasDownloadDir = false
                this.defaultClientName = ''
                this.loadingDownloadDir = true

                const defaultClient = await api.defaultClient()

                const downloadDir = defaultClient.fields.download_dir
                this.hasDownloadDir = downloadDir !== null && downloadDir !== undefined
                this.downloadDir = downloadDir || ''
                this.defaultClientName = defaultClient.name
            } catch (err) {
                console.log(err)
            } finally {
                this.loadingDownloadDir = false
            }
        },
        open () {
            this.topicUrl = null
            this.$refs.addTopicDialog.open()
            return this.defaultClient()
        },
        close () {
            this.$refs.addTopicDialog.close()
        },
        add () {
            this.close()
        }
    }
}
</script>

<style>
</style>

<template>
    <md-dialog ref="addTopicDialog">
        <md-dialog-title>Add Topic</md-dialog-title>

        <md-dialog-content style="width: 500px">
            <!-- Topic URL -->
            <md-layout md-gutter="24">
                <md-layout md-flex="100">
                    <md-input-container>
                        <label>URL</label>
                        <md-input v-model="topic.url"></md-input>
                    </md-input-container>
                </md-layout>
            </md-layout>
            <md-progress ref="topicProgress" md-indeterminate :style="{opacity: topic.loading ? 1: 0}"></md-progress>
            <!-- Topic Settings -->
            <mt-dynamic-form :form="topic.form"></mt-dynamic-form>

            <!-- Additional fields -->
            <!-- Download Dir -->
            <md-layout md-gutter="24">
                <md-layout md-flex="100">
                    <md-input-container :class="{'md-input-invalid': !additionalFields.downloadDir.loading && !additionalFields.downloadDir.support}">
                        <label>Download dir</label>
                        <md-input v-model="additionalFields.downloadDir.path" :disabled="additionalFields.downloadDir.loading || !additionalFields.downloadDir.support"></md-input>
                        <span v-if="!additionalFields.downloadDir.loading && !additionalFields.downloadDir.support" class="md-error" style="color: #ff5722">
                            {{additionalFields.downloadDir.defaultClientName}} doesn't support download dir settings
                        </span>
                    </md-input-container>
                </md-layout>
            </md-layout>
            <md-progress ref="downloadDirProgress" md-indeterminate :style="{opacity: additionalFields.downloadDir.loading ? 1: 0}"></md-progress>
        </md-dialog-content>

        <md-dialog-actions>
            <md-button class="md-primary" ref="addTopicDialogCancel" @click.native="close">Cancel</md-button>
            <md-button class="md-primary md-accent" ref="add" :disabled="loading || !complete" @click.native="add">Add</md-button>
        </md-dialog-actions>
    </md-dialog>
</template>

<script>
import api from '../../api/monitorrent'
import DynamicForm from '../DynamicForm.jsx'

export default {
    data: () => ({
        topic: {
            loading: false,
            url: '',
            form: {},
            parsed: false
        },
        additionalFields: {
            downloadDir: {
                complete: false,
                defaultClientName: null,
                loading: false,
                support: false,
                path: ''
            }
        }
    }),
    computed: {
        loading () {
            return this.topic.loading || this.additionalFields.downloadDir.loading
        },
        complete () {
            return this.topic.parsed && this.additionalFields.downloadDir.complete
        }
    },
    watch: {
        'topic.url' () {
            this.parseUrl()
        }
    },
    name: 'AddTopicDialog',
    components: {
        'mt-dynamic-form': DynamicForm
    },
    methods: {
        async parseUrl () {
            if (!this.topic.url) {
                this.topic.form = {rows: []}
                return
            }

            try {
                this.topic.loading = true
                this.topic.parsed = false
                const parseResult = await api.parseUrl(this.topic.url)
                this.topic.form = {rows: parseResult.form, model: parseResult.settings}
                this.topic.parsed = true
            } catch (err) {
                this.topic.form = {rows: []}
                console.log(err)
            } finally {
                this.topic.loading = false
            }
        },
        async defaultClient () {
            try {
                this.additionalFields.downloadDir.complete = false
                this.additionalFields.downloadDir.path = ''
                this.additionalFields.downloadDir.support = false
                this.additionalFields.downloadDir.defaultClientName = ''
                this.additionalFields.downloadDir.loading = true

                const defaultClient = await api.defaultClient()
                const downloadDir = defaultClient.fields.download_dir

                this.additionalFields.downloadDir.complete = true
                this.additionalFields.downloadDir.path = downloadDir || ''
                this.additionalFields.downloadDir.support = downloadDir !== null && downloadDir !== undefined
                this.additionalFields.downloadDir.defaultClientName = defaultClient.name
            } catch (err) {
                console.log(err)
            } finally {
                this.additionalFields.downloadDir.loading = false
            }
        },
        open () {
            this.topic.url = null
            this.$refs.addTopicDialog.open()
            return this.defaultClient()
        },
        close () {
            this.$refs.addTopicDialog.close()
        },
        add () {
            this.close()
            this.$emit('add-topic')
        }
    }
}
</script>

<style>
</style>

function renderText (h, data, state) {
    const onInput = (value) => {
        state.model[data.model] = value
    }

    return (<md-layout md-flex={data.flex} ref={data.model}>
            <md-input-container>
                <label>{data.label}</label>
                <md-input ref={`input-${data.model}`} type={data.type} value={state.model[data.model]} onInput={onInput}></md-input>
            </md-input-container>
        </md-layout>)
}

function renderSelect (h, data, state) {
    const onInput = (value) => {
        state.model[data.model] = value
    }

    return (<md-layout md-flex={data.flex} ref={data.model}>
            <md-input-container>
                <label>{data.label}</label>
                <md-select ref={`input-${data.model}`} value={state.model[data.model]} onInput={onInput}>
                    {data.options.map(o => (<md-option value={o}>{o}</md-option>))}
                </md-select>
            </md-input-container>
        </md-layout>)
}

function renderRow (h, data, state) {
    const ref = `row${state.row++}`
    return (<md-layout md-gutter={state.gutter} ref={ref}>
            {data.content.map(c => renderContent(h, c, state))}
        </md-layout>)
}

const contentFactory = {
    'row': renderRow,
    'password': renderText,
    'text': renderText,
    'number': renderText,
    'select': renderSelect
}

function renderContent (h, data, state) {
    const factory = contentFactory[data.type]
    if (factory) {
        return factory(h, data, state)
    }
}

export default {
    name: 'mtDynamicForm',
    props: {
        'rows': {
            type: Array,
            default: []
        },
        'gutter': {
            type: Number,
            default: 24
        }
    },
    watch: {
        rows: newRows => updateRows(newRows)
    },
    data: () => ({
        model: {}
    }),
    methods: {
        updateRows(rows) {
            const newModel = {}
            for (let row of rows) {
                for (let content of row.content) {
                    if (content.model) {
                        newModel[content.model] = content.value || null
                    }
                }
            }
            this.$set(this, 'model', newModel)
        }
    },
    created () {
        this.updateRows(this.rows)
    },
    render (h) {
        let state = {row: 0, gutter: this.gutter, model: this.model}
        return (<div>
                {this.rows.map(r => renderContent(h, r, state))}
            </div>)
    }
}

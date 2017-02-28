function renderText (h, data, state) {
    const props = {
        type: data.type
    }
    if (data.value) {
        props.value = data.value
    }

    return (<md-layout md-flex={data.flex} ref={data.model}>
            <md-input-container>
                <label>{data.label}</label>
                <md-input {...{props}}></md-input>
            </md-input-container>
        </md-layout>)
}

function renderSelect (h, data, state) {
    return (<md-layout md-flex={data.flex} ref={data.model}>
            <md-input-container>
                <label>{data.label}</label>
                <md-select>
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
    props: {
        'rows': {
            type: Array,
            required: true
        },
        'gutter': {
            type: Number,
            default: 24
        }
    },
    name: 'mtDynamicForm',
    render (h) {
        let state = {row: 0, gutter: this.gutter}
        return (<div>
                {this.rows.map(r => renderContent(h, r, state))}
            </div>)
    }
}

export default function Input({

    value,

    onChange,

    placeholder

}){

    return(

        <input

            value={value}

            onChange={onChange}

            placeholder={placeholder}

        />

    )

}
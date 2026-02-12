# React JS

## Notes

### Mental Model
    DOM        → Whiteboard
    HTML       → Initial notes written on the board
    JavaScript → The marker (writes / erases directly)
    React      → The editor who updates it efficiently
    
### DOM (Document Object Model)
    Browser's live in memory representation
    Mental Model: 
        The DOM is the browser’s tree of UI objects.
        React is a UI calculator that keeps that tree in sync with state.

### Single Page Applications: 
    One Template but updating components of the DOM

### Componets
    Visual layer of the UI
    Header, Navigation Bar, Sidebar, Footer, .etc
    Components Function name must be capitalized with snakecase
    Components can only return one parent / root element 
        Fragment: <> ... </>

### JSX (JavaScript XML)

### URL Router
    Keep UI in sync with a router

### Props
    Pass components down from another
    Parent Child relationship
    Prop Drilling: Props can be passed down unlimited number of times

### State
    Javascript Object
    Represents information / "state" of a component
    Update State

### Component Lifecycle
    Initialization → Mounting → Updating → Unmounting
    Component: Mounting → Updating → Unmounting
    Class Components:
        componentDidMount(){}
        componentDidUpdate(){}
        componentWillUnmount(){}

### Hooks
    Add State to Functional Components
    Hooks are functions that allow us to hook into and manage state
    Common Hooks:
        useState()  // Set & Update State
        useEffect() // Perform side effects in lifecycle

### State Management
    Tech: Context API, Redux
    So we dont have to manage prop drilling

### Virtual DOM
    Verify Changes to the "real" DOM and only update required components

### Key Prop
    List needs to have "key" prop

### Event Listeners
    Handling events
    <li onClick={openNote}>

### Handling Forms
    Examples: <input>, <textarea>, <select>
    <form onSubmit={handleSubmit}>
        <input type="text" onChange={updateNoteValue} value={note} />
        <input type="submit" />
    </form>

### Conditional Rendering
    Rendering an element if a condition is met
    Example: Display user's name if logged in, else display request to login

### Common Commands
    npx create-react-app <appname> // Sets up your development environment
    npm start // Starts up development server
    npm run build // Creates an optimized build of your app

## Questions
    What is the difference between hooks and event listeners

## References
[Youtube: Fireship - React in 100 Seconds](https://www.youtube.com/watch?v=Tn6-PIqc4UM) 

[Youtube: Nova_Designs_ - Master React JS in easy way](https://youtu.be/E8lXC2mR6-k?si=cLj8dgs4d1-kgIVs) 

[Youtube: Dennis Ivy - React JS Explained in 10 Minutes](https://www.youtube.com/watch?v=s2skans2dP4)

[Youtube: Code Bootcamp - Every React Component Explained in 12 Minutes](https://www.youtube.com/watch?v=wIyHSOugGGw)

[Github: alan2207 / bulletprood-react / docs / project-structure.md](https://github.com/alan2207/bulletproof-react/blob/master/docs/project-structure.md)

[Github: Airbnb React/JSX Style Guide](https://github.com/airbnb/javascript/tree/master/react)

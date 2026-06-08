interface Pet {
    void play();
}
public class Animal {
    void eat() {
        System.out.println("Eating...");
    }
    void sleep() {
        System.out.println("Sleeping...");
    }
}
class Dog extends Animal implements Pet {
    void sound() {
        System.out.println("Barking...");
    }

    @Override
    public void play() {
        System.out.println("Dog is playing fetch...");
    }
}
class DBreeds extends Dog {
    void breedInfo() {
        System.out.println("This is a specific breed of dog.");
    }
}
class Cat extends Animal implements Pet {
    void sound() {
        System.out.println("Meowing...");
    }

    @Override
    public void play() {
        System.out.println("Cat is playing with a yarn ball...");
    }
}
class Main {
    public static void main(String[] args) {
        Dog dog = new Dog();
        DBreeds breeds = new DBreeds();
        Cat cat = new Cat();
        breeds.eat(); 
        breeds.sleep();
        breeds.sound();
        breeds.breedInfo();
        breeds.play();
        cat.eat();
        cat.sleep();
        cat.sound();
        cat.play(); 
    }
}
@FunctionalInterface
interface Calculator{
    int operate(int a,int b);
}
public class Lemda {
    public static void main(String[] args) {
        
       Calculator addition = (a,b) -> (a+b);
       System.out.println("the addition of 6 and 7 is"+addition.operate(6, 7));
    }
}
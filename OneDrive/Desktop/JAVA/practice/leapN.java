public class leapN {
    static boolean isLeapN(int N) {
        if (N % 4 == 0) {
            if (N % 100 == 0) {
                return N % 400 == 0;
            }
            return true;
        }
        return false;
    }
}

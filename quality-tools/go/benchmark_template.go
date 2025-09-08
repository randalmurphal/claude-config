package benchmark_examples

import (
	"math/big"
	"testing"
	"time"

	"github.com/shopspring/decimal"
)

// Example: Benchmark different decimal calculation methods
// Critical for financial applications

func BenchmarkDecimalAddition_Float64(b *testing.B) {
	price := 123.456789
	spread := 0.000012
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = price + spread
	}
}

func BenchmarkDecimalAddition_Decimal(b *testing.B) {
	price := decimal.NewFromFloat(123.456789)
	spread := decimal.NewFromFloat(0.000012)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = price.Add(spread)
	}
}

func BenchmarkDecimalAddition_BigFloat(b *testing.B) {
	price := big.NewFloat(123.456789)
	spread := big.NewFloat(0.000012)
	result := new(big.Float)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		result.Add(price, spread)
	}
}

// Example: Benchmark order matching performance
type Order struct {
	ID        string
	Price     decimal.Decimal
	Quantity  decimal.Decimal
	Timestamp time.Time
	Side      string
}

func BenchmarkOrderMatching_Small(b *testing.B) {
	orders := generateOrders(100)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		matchOrders(orders)
	}
}

func BenchmarkOrderMatching_Medium(b *testing.B) {
	orders := generateOrders(1000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		matchOrders(orders)
	}
}

func BenchmarkOrderMatching_Large(b *testing.B) {
	orders := generateOrders(10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		matchOrders(orders)
	}
}

// Example: Benchmark concurrent operations
func BenchmarkConcurrentPriceUpdate(b *testing.B) {
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			updatePrice(decimal.NewFromFloat(123.45))
		}
	})
}

// Example: Memory allocation benchmark
func BenchmarkMemoryAllocation_Slice(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		slice := make([]decimal.Decimal, 0, 1000)
		for j := 0; j < 1000; j++ {
			slice = append(slice, decimal.NewFromFloat(float64(j)))
		}
	}
}

func BenchmarkMemoryAllocation_PreAllocated(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		slice := make([]decimal.Decimal, 1000)
		for j := 0; j < 1000; j++ {
			slice[j] = decimal.NewFromFloat(float64(j))
		}
	}
}

// Example: Latency-sensitive operations
func BenchmarkLatencyCritical_OrderExecution(b *testing.B) {
	order := Order{
		ID:       "TEST001",
		Price:    decimal.NewFromFloat(123.45),
		Quantity: decimal.NewFromFloat(1000),
		Side:     "BUY",
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		start := time.Now()
		executeOrder(order)
		elapsed := time.Since(start)
		
		// Track if execution exceeds acceptable latency
		if elapsed > 100*time.Microsecond {
			b.Fatalf("Execution too slow: %v", elapsed)
		}
	}
}

// Benchmark table-driven tests
func BenchmarkSpreadCalculation(b *testing.B) {
	testCases := []struct {
		name string
		bid  decimal.Decimal
		ask  decimal.Decimal
	}{
		{"tight_spread", decimal.NewFromFloat(1.12345), decimal.NewFromFloat(1.12346)},
		{"normal_spread", decimal.NewFromFloat(1.12345), decimal.NewFromFloat(1.12355)},
		{"wide_spread", decimal.NewFromFloat(1.12345), decimal.NewFromFloat(1.12445)},
	}
	
	for _, tc := range testCases {
		b.Run(tc.name, func(b *testing.B) {
			for i := 0; i < b.N; i++ {
				_ = tc.ask.Sub(tc.bid)
			}
		})
	}
}

// Helper functions (implement these based on your actual code)
func generateOrders(n int) []Order {
	orders := make([]Order, n)
	for i := 0; i < n; i++ {
		orders[i] = Order{
			Price:    decimal.NewFromFloat(100.0 + float64(i)),
			Quantity: decimal.NewFromFloat(1000),
		}
	}
	return orders
}

func matchOrders(orders []Order) {
	// Implement order matching logic
}

func updatePrice(price decimal.Decimal) {
	// Implement price update logic
}

func executeOrder(order Order) {
	// Implement order execution logic
}

/*
Usage Tips:
1. Run benchmarks: go test -bench=. -benchmem
2. Compare benchmarks: go test -bench=. -benchmem -count=10 > new.txt && benchstat old.txt new.txt
3. Profile CPU: go test -bench=. -cpuprofile=cpu.prof && go tool pprof cpu.prof
4. Profile Memory: go test -bench=. -memprofile=mem.prof && go tool pprof mem.prof
5. Run specific benchmark: go test -bench=BenchmarkDecimal
6. Set benchmark time: go test -bench=. -benchtime=10s
7. Benchmark with race detector: go test -bench=. -race (slower but finds races)
*/
